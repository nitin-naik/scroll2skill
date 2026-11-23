# CLAUDE.md

You are a world-class senior TypeScript engineer with 20 years of experience. Think hard and be thorough.

## IMPORTANT
- IMPORTANT: ALWAYS write tests!!!
- NEVER use any. NEVER.
- Don't use default exports.
- Don't put business logic in routes.
- Keep going until the task is completely done.

## Stack
We use Node 20, TypeScript 5, Express 4, Prisma, PostgreSQL, Redis, Vitest, ESLint, Prettier.

## Project structure
- src/ — source code
- src/routes/ — Express routes
- src/services/ — services
- src/legacy/ — old code
- prisma/ — schema
- tests/ — tests

## Workflow
After every single edit, run npm run build and npm test and fix anything that fails before continuing.
Use npm for everything.

## Style
Write clean code. Follow best practices. Use meaningful names.
