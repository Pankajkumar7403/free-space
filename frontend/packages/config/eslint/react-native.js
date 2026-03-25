// 📍 LOCATION: free-space/frontend/packages/config/eslint/react-native.js
/** @type {import("eslint").Linter.Config} */
module.exports = {
    extends: [
      'universe/native',
      'plugin:@typescript-eslint/recommended-type-checked',
      'prettier',
    ],
    plugins: ['@typescript-eslint', 'import'],
    parser: '@typescript-eslint/parser',
    rules: {
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/no-non-null-assertion': 'error',
      '@typescript-eslint/consistent-type-imports': ['error', { prefer: 'type-imports' }],
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      'import/no-cycle': 'error',
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      // React Native specific
      'react-native/no-unused-styles': 'error',
      'react-native/no-color-literals': 'warn', // Enforce design tokens
    },
  };
  