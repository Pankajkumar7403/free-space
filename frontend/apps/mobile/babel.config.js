// 📍 LOCATION: free-space/frontend/apps/mobile/babel.config.js
module.exports = function (api) {
    api.cache(true);
    return {
      presets: ['babel-preset-expo'],
      plugins: [
        // NativeWind v4 requires this plugin
        'nativewind/babel',
        // Required for Reanimated
        'react-native-reanimated/plugin',
      ],
    };
  };