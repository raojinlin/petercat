import axios from "axios";
import { LLMTokenInsert } from "../hooks/useToken";

const apiDomain = process.env.NEXT_PUBLIC_API_DOMAIN;

export async function getTokenList() {
  const response = await axios.get(`${apiDomain}/api/user/llm_tokens`);
  return response.data.data;
}

export async function deleteToken(id: string) {
  const response = await axios.delete(`${apiDomain}/api/user/llm_token/${id}`);
  return response.data;
}

export async function createToken(data: LLMTokenInsert) {
  const response = await axios.post(`${apiDomain}/api/user/llm_token`, data);
  return response.data;
}