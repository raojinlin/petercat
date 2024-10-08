import boto3
import io
import os
import toml
import argparse
import yaml

S3_BUCKET = "petercat-env-variables"
ENV_FILE = ".env"

current_dir = os.path.dirname(os.path.abspath(__file__))
LOCAL_ENV_FILE = os.path.join(current_dir, "..", ".env")

s3 = boto3.resource("s3")
s3_client = boto3.client("s3")


def confirm_action(message):
    """二次确认函数"""
    while True:
        response = input(f"{message} (y/n): ").lower()
        if response == "y":
            return True
        elif response == "n":
            return False
        else:
            print("请输入 'y' 或 'n'.")


def pull_envs(args):
    if args.silence or confirm_action("确认从远端拉取 .env 文件么"):
        obj = s3.Object(S3_BUCKET, ENV_FILE)
        data = io.BytesIO()
        obj.download_fileobj(data)
        with open(LOCAL_ENV_FILE, "wb") as f:
            f.write(data.getvalue())
        print("拉取完毕")


def push_envs(args):
    class ProgressPercentage(object):
        def __init__(self, filename):
            self._filename = filename
            self._size = float(os.path.getsize(filename))
            self._seen_so_far = 0
            self._lock = None

        def __call__(self, bytes_amount):
            # To simplify, we'll ignore multi-threading here.
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            print(
                f"\r{self._filename}: {self._seen_so_far} bytes transferred out of {self._size} ({percentage:.2f}%)",
                end="\n",
            )

    if args.silence or confirm_action("确认将本地 .env 文件上传到远端么"):
        s3_client.upload_file(
            LOCAL_ENV_FILE,
            S3_BUCKET,
            ENV_FILE,
            Callback=ProgressPercentage(LOCAL_ENV_FILE),
        )
        print("上传成功")


def snake_to_camel(snake_str):
    """Convert snake_case string to camelCase."""
    components = snake_str.lower().split("_")
    # Capitalize the first letter of each component except the first one
    return "".join(x.title() for x in components)


def load_env_file(env_file):
    """Load the .env file and return it as a dictionary with camelCase keys."""
    env_vars = {}
    with open(env_file, "r") as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith("#"):  # Skip empty lines and comments
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()
    return env_vars

class Ref:
    """Custom representation for CloudFormation !Ref."""

    def __init__(self, ref):
        self.ref = ref


def ref_representer(dumper, data):
    """Custom YAML representer for CloudFormation !Ref."""
    return dumper.represent_scalar("!Ref", data.ref, style="")


def update_cloudformation_environment(
    env_vars={}, cloudformation_template="template.yml"
):
    """Update Environment Variables in CloudFormation template to use Parameters."""

    def cloudformation_tag_constructor(loader, tag_suffix, node):
        """Handle CloudFormation intrinsic functions like !Ref, !GetAtt, etc."""
        return loader.construct_scalar(node)

    # Register constructors for CloudFormation intrinsic functions
    yaml.SafeLoader.add_multi_constructor("!", cloudformation_tag_constructor)
    yaml.SafeDumper.add_representer(Ref, ref_representer)

    with open(cloudformation_template, "r") as file:
        template = yaml.safe_load(file)

    # Update environment variables in the resources
    for resource in template.get("Resources", {}).values():
        if "Properties" in resource and "Environment" in resource["Properties"]:
            env_vars_section = resource["Properties"]["Environment"].get(
                "Variables", {}
            )
            for key in env_vars_section:
                if key in env_vars:
                    env_vars_section[key] = env_vars[key]

    # Save the updated CloudFormation template
    with open(cloudformation_template, "w") as file:
        yaml.safe_dump(template, file, default_style=None, default_flow_style=False)


def load_config_toml(toml_file):
    """Load the config.toml file and return its content as a dictionary."""
    with open(toml_file, "r") as file:
        config = toml.load(file)
    return config


def update_parameter_overrides(config, env_vars):
    """Update the parameter_overrides in the config dictionary with values from env_vars."""
    parameter_overrides = [f"{key}={value}" for key, value in env_vars.items()]
    config["default"]["deploy"]["parameters"][
        "parameter_overrides"
    ] = parameter_overrides
    return config


def save_config_toml(config, toml_file):
    """Save the updated config back to the toml file."""
    with open(toml_file, "w") as file:
        toml.dump(config, file)


def update_config_with_env(args):
    env_file = args.env or LOCAL_ENV_FILE
    """Load env vars from a .env file and update them into a config.toml file."""
    pull_envs(args)

    env_vars = load_env_file(env_file)

    update_cloudformation_environment(env_vars)


def main():
    parser = argparse.ArgumentParser(
        description="Update config.toml parameter_overrides with values from a .env file."
    )

    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Sub-command help"
    )
    pull_parser = subparsers.add_parser(
        "pull", help="Pull environment variables from a .env file"
    )
    pull_parser.add_argument(
        "--silence",
        action="store_true",
        help="Skip confirmation before updating the CloudFormation template",
    )
    pull_parser.set_defaults(handle=pull_envs)

    push_parser = subparsers.add_parser(
        "push", help="Push enviroment variables from local .env file to Remote"
    )
    push_parser.add_argument(
        "--silence",
        action="store_true",
        help="Skip confirmation before updating the CloudFormation template",
    )
    push_parser.set_defaults(handle=push_envs)

    build_parser = subparsers.add_parser(
        "build",
        help="Pull environment variables from a .env file and update samconfig.toml",
    )
    build_parser.set_defaults(handle=update_config_with_env)

    build_parser.add_argument(
        "-e",
        "--env",
        type=str,
        default=LOCAL_ENV_FILE,
        help="Path to the .env file (default: .env)",
    )
    build_parser.add_argument(
        "--silence",
        action="store_true",
        help="Skip confirmation before updating the CloudFormation template",
    )

    args = parser.parse_args()
    if args.command is not None:
        args.handle(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
