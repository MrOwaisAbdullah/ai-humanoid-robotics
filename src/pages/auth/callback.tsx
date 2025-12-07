import React, { useEffect } from 'react';
import Head from '@docusaurus/Head';
import { OAuthCallbackHandler } from '../../../src/contexts/AuthContext';

export default function AuthCallbackPage() {
  return (
    <>
      <Head>
        <title>Authentication Callback</title>
        <meta name="description" content="Processing authentication..." />
      </Head>
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <OAuthCallbackHandler />
      </div>
    </>
  );
}