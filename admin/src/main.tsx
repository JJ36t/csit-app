import React from 'react';
import ReactDOM from 'react-dom/client';
import { ConfigProvider } from 'antd';
import arEG from 'antd/locale/ar_EG';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider
      locale={arEG}
      direction="rtl"
      theme={{ token: { colorPrimary: '#1f4e79', borderRadius: 8 } }}
    >
      <App />
    </ConfigProvider>
  </React.StrictMode>,
);
