// 📍 LOCATION: free-space/frontend/commitlint.config.js
/** @type {import('@commitlint/types').UserConfig} */
module.exports = {
    extends: ['@commitlint/config-conventional'],
    rules: {
      // Scopes must match sprint/app names
      'scope-enum': [
        2,
        'always',
        [
          // Apps
          'web',
          'mobile',
          // Packages
          'types',
          'api-client',
          'validators',
          'ui-kit',
          'hooks',
          'config',
          'test-utils',
          // Infrastructure
          'ci',
          'turbo',
          'deps',
          'docs',
        ],
      ],
      'type-enum': [
        2,
        'always',
        ['feat', 'fix', 'refactor', 'test', 'chore', 'docs', 'perf', 'ci', 'revert'],
      ],
      'subject-case': [2, 'never', ['upper-case', 'pascal-case', 'start-case']],
      'header-max-length': [2, 'always', 100],
    },
  };