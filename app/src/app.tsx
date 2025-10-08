import React from 'react';

import { LocalStorageClient, Requester } from '@kibalabs/core';
import { IRoute, MockStorage, Router, SubRouter, useInitialization } from '@kibalabs/core-react';
import { KibaApp } from '@kibalabs/ui-react';

import { LongevityClient } from './client/client';
import { GlobalsProvider, IGlobals } from './GlobalsContext';
import { PageDataProvider } from './PageDataContext';
import { HomePage } from './pages/HomePage';
import { buildAppTheme } from './theme';

declare global {
  export interface Window {
    KRT_API_URL?: string;
  }
}

const requester = new Requester();
const baseUrl = typeof window !== 'undefined' && window.KRT_API_URL ? window.KRT_API_URL : 'http://localhost:8000';
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
    <KibaApp theme={theme} isFullPageApp={true} extraGlobalCss={extraGlobalCss}>
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
  );
}
