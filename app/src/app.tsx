import React from 'react';

import { LocalStorageClient, Requester } from '@kibalabs/core';
import { IRoute, MockStorage, Router, SubRouter, useInitialization } from '@kibalabs/core-react';
import { ComponentDefinition, KibaApp } from '@kibalabs/ui-react';
import { buildDropzoneThemes, Dropzone, DropzoneThemedStyle } from '@kibalabs/ui-react-dropzone';
import { buildToastThemes, Toast, ToastThemedStyle } from '@kibalabs/ui-react-toast';

import { LongevityClient } from './client/client';
import { GlobalsProvider, IGlobals } from './GlobalsContext';
import { PageDataProvider } from './PageDataContext';
import { HomePage } from './pages/HomePage';
import { ResultsPage } from './pages/ResultsPage';
import { UploadPage } from './pages/UploadPage';
import { buildAppTheme } from './theme';

declare global {
  export interface Window {
    KRT_API_URL?: string;
  }
}

const requester = new Requester();
const baseUrl = typeof window !== 'undefined' && window.KRT_API_URL ? window.KRT_API_URL : 'https://longevityhack-api.kibalabs.com';
const longevityClient = new LongevityClient(requester, baseUrl);
const localStorageClient = new LocalStorageClient(typeof window !== 'undefined' ? window.localStorage : new MockStorage());
const sessionStorageClient = new LocalStorageClient(typeof window !== 'undefined' ? window.sessionStorage : new MockStorage());
const theme = buildAppTheme();

const globals: IGlobals = {
  requester,
  localStorageClient,
  sessionStorageClient,
  longevityClient,
};

const routes: IRoute<IGlobals>[] = [
  { path: '/', page: HomePage },
  { path: '/upload', page: UploadPage },
  { path: '/results', page: ResultsPage },
];

interface IAppProps {
  staticPath?: string;
  pageData?: unknown | undefined | null;
}

const extraGlobalCss = `
table td, table th {
  border: 1px solid var(--color-background-light05);
  padding: 0.5em 1em;
}

table tr:nth-child(even){
  background-color: var(--color-background-light05);
}

table th {
  padding-top: 12px;
  padding-bottom: 12px;
  text-align: left;
  font-weight: bold;
  border-bottom: 1px solid var(--color-brand-primary);
}
`;

// @ts-expect-error
const extraComponentDefinitions: ComponentDefinition[] = [{
  component: Dropzone,
  themeMap: buildDropzoneThemes(theme.colors, theme.dimensions, theme.texts, theme.boxes),
  themeCssFunction: DropzoneThemedStyle,
}, {
  component: Toast,
  themeMap: buildToastThemes(theme.colors, theme.dimensions, theme.boxes, theme.texts, theme.icons),
  themeCssFunction: ToastThemedStyle,
}];


export function App(props: IAppProps): React.ReactElement {
  const isInitialized = useInitialization((): void => {
    if (typeof window !== 'undefined') {
      const searchParams = new URLSearchParams(window.location.search);
      const referrer = searchParams.get('referrer');
      if (referrer) {
        localStorageClient.setValue('referrer', referrer);
      }
    }
  });

  return (
    <div style={{
      position: 'relative',
      minHeight: '100vh',
    }}>
      {/* Animated background */}
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        background: '#fce4ec',
        zIndex: 0,
      }}>
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          backgroundImage: `
            radial-gradient(circle at 20% 30%, rgba(250, 208, 196, 0.8) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(255, 209, 255, 0.7) 0%, transparent 50%),
            radial-gradient(circle at 40% 70%, rgba(224, 195, 252, 0.8) 0%, transparent 50%),
            radial-gradient(circle at 90% 80%, rgba(251, 194, 235, 0.7) 0%, transparent 50%),
            radial-gradient(circle at 10% 90%, rgba(248, 181, 213, 0.7) 0%, transparent 50%),
            radial-gradient(circle at 60% 50%, rgba(255, 230, 250, 0.6) 0%, transparent 60%)
          `,
          backgroundRepeat: 'no-repeat',
          backgroundSize: 'cover',
          animation: 'morphGradient 20s ease-in-out infinite',
          pointerEvents: 'none',
        }} />
      </div>

      <style>{`
        @keyframes morphGradient {
          0%, 100% {
            transform: translate(0, 0) scale(1);
            opacity: 1;
          }
          33% {
            transform: translate(5%, -5%) scale(1.1);
            opacity: 0.9;
          }
          66% {
            transform: translate(-5%, 5%) scale(1.05);
            opacity: 0.95;
          }
        }

        /* Override KibaApp background */
        .kiba-app, .kiba-app > div {
          background: transparent !important;
        }
      `}</style>

      <div style={{ position: 'relative', zIndex: 1 }}>
        <KibaApp theme={theme} isFullPageApp={true} extraComponentDefinitions={extraComponentDefinitions} extraGlobalCss={extraGlobalCss}>
          <PageDataProvider initialData={props.pageData}>
            <GlobalsProvider globals={globals}>
              <Router staticPath={props.staticPath}>
                {isInitialized && (
                  <SubRouter routes={routes} />
                )}
              </Router>
            </GlobalsProvider>
          </PageDataProvider>
        </KibaApp>
      </div>
    </div>
  );
}
