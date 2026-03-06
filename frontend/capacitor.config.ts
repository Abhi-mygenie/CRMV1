import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.crmmygenie.app',
  appName: 'MyGenie CRM',
  webDir: 'build',
  server: {
    androidScheme: 'https'
  },
  plugins: {
    SplashScreen: {
      launchAutoHide: true,
      launchShowDuration: 2000,
      launchFadeOutDuration: 500,
      backgroundColor: '#F26B33',
      showSpinner: false,
      androidScaleType: 'CENTER_CROP',
      splashFullScreen: true,
      splashImmersive: true
    },
    StatusBar: {
      backgroundColor: '#F26B33',
      style: 'LIGHT',
      overlaysWebView: false
    },
    PushNotifications: {
      presentationOptions: ['badge', 'sound', 'alert']
    },
    Camera: {
      permissions: ['camera', 'photos']
    }
  }
};

export default config;
