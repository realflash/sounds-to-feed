# Configuration Templates

This directory contains the "Gold Standard" configuration files to be copied or extended by new products.

## Usage

### Prettier
Copy `prettierrc.json` to `.prettierrc` in the project root.
Ensure `prettier` and `prettier-plugin-tailwindcss` are installed.

### Python (Ruff)
Copy `ruff.toml` to `ruff.toml` or append its content to `pyproject.toml`.

### TypeScript
Extend `tsconfig.base.json` in your project's `tsconfig.json`:
```json
{
  "extends": "./path/to/standards/tsconfig.base.json",
  "compilerOptions": {
     "baseUrl": "."
  }
}
```
(Or just copy the contents if the standards repo is not a dependency).
