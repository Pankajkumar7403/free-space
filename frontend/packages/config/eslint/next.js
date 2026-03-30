// 📍 LOCATION: free-space/frontend/packages/config/eslint/next.js
/** @type {import("eslint").Linter.Config} */
module.exports = {
    extends: [
      'next/core-web-vitals',
      'next/typescript',
      'plugin:@typescript-eslint/recommended-type-checked',
      'plugin:@typescript-eslint/stylistic-type-checked',
      'plugin:jsx-a11y/recommended',
      'prettier',
    ],
    plugins: ['@typescript-eslint', 'jsx-a11y', 'import'],
    parser: '@typescript-eslint/parser',
    rules: {
      // TypeScript — strict rules that match our roadmap standards
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/no-non-null-assertion': 'error',
      '@typescript-eslint/consistent-type-imports': ['error', { prefer: 'type-imports' }],
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      '@typescript-eslint/no-floating-promises': 'error',
      '@typescript-eslint/await-thenable': 'error',
  
      // React
      'react/self-closing-comp': 'error',
      'react/jsx-curly-brace-presence': ['error', { props: 'never', children: 'never' }],
  
      // Imports — enforce package boundaries
      'import/no-cycle': 'error',
      'import/no-default-export': 'off', // Next.js requires default exports for pages
      'no-console': ['warn', { allow: ['warn', 'error'] }],
  
      // Accessibility — mandatory for LGBTQ+ community platform
      'jsx-a11y/alt-text': 'error',
      'jsx-a11y/aria-props': 'error',
      'jsx-a11y/role-has-required-aria-props': 'error',
    },
    overrides: [
      {
        // Page files require default exports
        files: ['src/app/**/page.tsx', 'src/app/**/layout.tsx', 'src/app/**/error.tsx'],
        rules: { 'import/no-default-export': 'off' },
      },
    ],
  };
  