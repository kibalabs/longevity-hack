import React from 'react';

import { useNavigator } from '@kibalabs/core-react';
import { Alignment, Button, Direction, PaddingSize, Stack, Text } from '@kibalabs/ui-react';

import * as Resources from '../client/resources';
import { useGlobals } from '../GlobalsContext';

export function ResultsPage(): React.ReactElement {
  const navigator = useNavigator();
  const { longevityClient } = useGlobals();
  const [genomeAnalysis, setGenomeAnalysis] = React.useState<Resources.GenomeAnalysis | null>(null);
  const [genomeAnalysisResults, setGenomeAnalysisResults] = React.useState<Resources.GenomeAnalysisResult[] | null>(null);

  React.useEffect((): void => {
    // Get the analysis ID from URL query parameter
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get('id');
    if (id) {
      // Load analysis details
      longevityClient.getGenomeAnalysis(id).then((analysis: Resources.GenomeAnalysis): void => {
        setGenomeAnalysis(analysis);
      }).catch((error: Error): void => {
        console.error('Failed to fetch analysis:', error);
      });

      // Load results
      longevityClient.listGenomeAnalysisResults(id).then((results: Resources.GenomeAnalysisResult[]): void => {
        setGenomeAnalysisResults(results);
      }).catch((error: Error): void => {
        console.error('Failed to fetch results:', error);
      });
    } else {
      navigator.navigateTo('/');
    }
  }, [longevityClient, navigator]);

  if (!genomeAnalysisResults || !genomeAnalysis) {
    return (
      <Stack direction={Direction.Vertical} isFullWidth={true} isFullHeight={true} childAlignment={Alignment.Center} contentAlignment={Alignment.Center}>
        <Text variant='default'>Loading results...</Text>
      </Stack>
    );
  }

  return (
    <Stack direction={Direction.Vertical} shouldAddGutters={true} isFullWidth={true} isFullHeight={true} defaultGutter={PaddingSize.Wide2}>
      <Stack direction={Direction.Vertical} childAlignment={Alignment.Center} shouldAddGutters={true} paddingVertical={PaddingSize.Wide2}>
        <Text variant='header2'>Your Genetic Insights</Text>
        <Text variant='default'>{genomeAnalysis.fileName}</Text>
      </Stack>

      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          width: '100%',
          maxWidth: '1200px',
          margin: '0 auto',
          paddingBottom: '100px',
        }}
      >
        <Stack direction={Direction.Vertical} shouldAddGutters={true} defaultGutter={PaddingSize.Wide2} isFullWidth={true}>
          {genomeAnalysisResults.map((result: Resources.GenomeAnalysisResult): React.ReactElement => (
            <div
              key={result.genomeAnalysisResultId}
              style={{
                backgroundColor: '#F9F9F9',
                borderRadius: '12px',
                border: '1px solid #E5E5E5',
                padding: '24px',
              }}
            >
              <Stack direction={Direction.Vertical} shouldAddGutters={true} defaultGutter={PaddingSize.Wide}>
                <Stack direction={Direction.Vertical} shouldAddGutters={true} defaultGutter={PaddingSize.Narrow}>
                  <Text variant='header3'>{result.phenotypeGroup}</Text>
                  <Text variant='default'>{result.phenotypeDescription}</Text>
                </Stack>

                <Stack direction={Direction.Vertical} shouldAddGutters={true} defaultGutter={PaddingSize.Wide}>
                  {result.snps.map((snp: Resources.SNP): React.ReactElement => (
                    <div
                      key={snp.rsid}
                      style={{
                        backgroundColor: 'white',
                        borderRadius: '8px',
                        border: '1px solid #E5E5E5',
                        padding: '16px',
                      }}
                    >
                      <Stack direction={Direction.Vertical} shouldAddGutters={true} defaultGutter={PaddingSize.Default}>
                        <Stack direction={Direction.Horizontal} shouldAddGutters={true} contentAlignment={Alignment.Start} defaultGutter={PaddingSize.Default}>
                          <Text variant='bold'>{snp.rsid}</Text>
                          <Text variant='note'>•</Text>
                          <Text variant='note'>
                            Genotype:
                            {snp.genotype}
                          </Text>
                        </Stack>
                        <Text variant='default'>{snp.annotation}</Text>
                        <Text variant='note' tag='em'>
                          Confidence:
                          {snp.confidence}
                        </Text>
                        <Text variant='note'>
                          Sources:
                          {snp.sources.join(', ')}
                        </Text>
                      </Stack>
                    </div>
                  ))}
                </Stack>
              </Stack>
            </div>
          ))}
        </Stack>
      </div>

      <div
        style={{
          position: 'sticky',
          bottom: 0,
          backgroundColor: 'white',
          borderTop: '1px solid #E5E5E5',
          padding: '16px',
          zIndex: 10,
        }}
      >
        <Stack
          direction={Direction.Horizontal}
          childAlignment={Alignment.Center}
          contentAlignment={Alignment.Center}
          shouldAddGutters={true}
          defaultGutter={PaddingSize.Wide}
        >
          <Button variant='primary' text='Upload Another File' onClicked={(): void => navigator.navigateTo('/')} />
          <Button variant='secondary' text='Back to Home' onClicked={(): void => navigator.navigateTo('/')} />
        </Stack>
      </div>
    </Stack>
  );
}
