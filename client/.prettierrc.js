module.exports = { 
  endOfLine: 'lf',
  semi: true,
  singleQuote: true,
  tabWidth: 2,
  trailingComma: 'all',
  printWidth: 80,
  arrowParens: 'always',
  proseWrap: 'never',
  overrides: [
    { files: '.eslintrc', options: { 'parser': 'json' } },
    { files: '.prettierrc', options: { 'parser': 'json' } }
  ]
}
