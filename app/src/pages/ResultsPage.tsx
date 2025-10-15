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
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty array - only run once on mount

  if (!genomeAnalysisResults || !genomeAnalysis) {
    return (
      <Stack direction={Direction.Vertical} isFullWidth={true} isFullHeight={true} childAlignment={Alignment.Center} contentAlignment={Alignment.Center}>
        <Text variant='default'>Loading results...</Text>
      </Stack>
    );
  }

  return (
    <Stack direction={Direction.Vertical} shouldAddGutters={true} isFullWidth={true} isFullHeight={true} defaultGutter={PaddingSize.Wide2}>
      {/* Header Section */}
      <Stack direction={Direction.Vertical} childAlignment={Alignment.Center} shouldAddGutters={true} paddingVertical={PaddingSize.Wide2} paddingHorizontal={PaddingSize.Wide}>
        <Text variant='header1'>🧬 Your Genetic Insights</Text>
        <Text variant='default'>{genomeAnalysis.fileName}</Text>
        {genomeAnalysis.detectedFormat && (
          <Text variant='note'>Detected Format: {genomeAnalysis.detectedFormat}</Text>
        )}

        {/* Summary Stats */}
        {genomeAnalysis.summary && (
          <Stack direction={Direction.Horizontal} shouldAddGutters={true} defaultGutter={PaddingSize.Wide2} paddingTop={PaddingSize.Wide} contentAlignment={Alignment.Center} childAlignment={Alignment.Center}>
            <Stack direction={Direction.Vertical} childAlignment={Alignment.Center} shouldAddGutters={true} defaultGutter={PaddingSize.Narrow}>
              <Text variant='header2'>{genomeAnalysis.summary.totalSnps?.toLocaleString() || 'N/A'}</Text>
              <Text variant='note'>Total SNPs</Text>
            </Stack>
            <div style={{ width: '1px', height: '40px', backgroundColor: '#E5E5E5' }} />
            <Stack direction={Direction.Vertical} childAlignment={Alignment.Center} shouldAddGutters={true} defaultGutter={PaddingSize.Narrow}>
              <Text variant='header2'>{genomeAnalysis.summary.matchedSnps?.toLocaleString() || 'N/A'}</Text>
              <Text variant='note'>Matched Associations</Text>
            </Stack>
            <div style={{ width: '1px', height: '40px', backgroundColor: '#E5E5E5' }} />
            <Stack direction={Direction.Vertical} childAlignment={Alignment.Center} shouldAddGutters={true} defaultGutter={PaddingSize.Narrow}>
              <Text variant='header2'>{genomeAnalysis.summary.clinvarCount?.toLocaleString() || 'N/A'}</Text>
              <Text variant='note'>Clinical Variants</Text>
            </Stack>
          </Stack>
        )}
      </Stack>

      {/* Results Content */}
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
        <Stack direction={Direction.Vertical} shouldAddGutters={true} defaultGutter={PaddingSize.Wide3} isFullWidth={true} paddingHorizontal={PaddingSize.Wide}>
          {genomeAnalysisResults.map((result: Resources.GenomeAnalysisResult): React.ReactElement => (
            <div key={result.genomeAnalysisResultId}>
              {/* Category Header */}
              <Stack direction={Direction.Vertical} shouldAddGutters={true} defaultGutter={PaddingSize.Default} paddingBottom={PaddingSize.Wide}>
                <Text variant='header2'>{result.phenotypeGroup}</Text>
                <Text variant='default'>{result.phenotypeDescription}</Text>
                <div style={{ width: '60px', height: '3px', backgroundColor: '#007AFF', borderRadius: '2px' }} />
              </Stack>

              {/* SNP Cards */}
              <Stack direction={Direction.Vertical} shouldAddGutters={true} defaultGutter={PaddingSize.Wide}>
                {result.snps.map((snp: Resources.SNP, index: number): React.ReactElement => (
                  <div
                    key={`${snp.rsid}-${index}`}
                    style={{
                      borderLeft: '3px solid #007AFF',
                      paddingLeft: '20px',
                      paddingTop: '12px',
                      paddingBottom: '12px',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <Stack direction={Direction.Vertical} shouldAddGutters={true} defaultGutter={PaddingSize.Default}>
                      {/* SNP Header */}
                      <Stack direction={Direction.Horizontal} shouldAddGutters={true} contentAlignment={Alignment.Start} defaultGutter={PaddingSize.Wide} childAlignment={Alignment.Center}>
                        <div style={{
                          backgroundColor: '#F0F5FF',
                          padding: '4px 12px',
                          borderRadius: '6px',
                          border: '1px solid #D0E0FF'
                        }}>
                          <Text variant='bold'>{snp.rsid}</Text>
                        </div>
                        <Stack direction={Direction.Horizontal} shouldAddGutters={true} defaultGutter={PaddingSize.Default} childAlignment={Alignment.Center}>
                          <Text variant='note'>Genotype:</Text>
                          <Text variant='default'>{snp.genotype}</Text>
                        </Stack>
                        {snp.importanceScore && (
                          <Stack direction={Direction.Horizontal} shouldAddGutters={true} defaultGutter={PaddingSize.Default} childAlignment={Alignment.Center}>
                            <Text variant='note'>Score:</Text>
                            <Text variant='default'>{snp.importanceScore.toFixed(1)}</Text>
                          </Stack>
                        )}
                      </Stack>

                      {/* Trait/Description */}
                      {snp.trait && (
                        <Text variant='default'>{snp.trait}</Text>
                      )}

                      {/* Details Row */}
                      <Stack direction={Direction.Horizontal} shouldAddGutters={true} defaultGutter={PaddingSize.Wide} childAlignment={Alignment.Center}>
                        {snp.effectStrength && snp.effectStrength.trim() && (
                          <div style={{
                            backgroundColor: snp.effectStrength.toLowerCase().includes('large') ? '#FFE5E5'
                              : snp.effectStrength.toLowerCase().includes('moderate') ? '#FFF5E5'
                              : '#E5F5FF',
                            color: snp.effectStrength.toLowerCase().includes('large') ? '#C00'
                              : snp.effectStrength.toLowerCase().includes('moderate') ? '#C60'
                              : '#06C',
                            padding: '2px 8px',
                            borderRadius: '4px',
                            fontSize: '12px',
                            fontWeight: 500
                          }}>
                            {snp.effectStrength} Effect
                          </div>
                        )}
                        {snp.pValue && (
                          <Text variant='note'>p-value: {snp.pValue}</Text>
                        )}
                        {snp.confidence && (
                          <Text variant='note'>Confidence: {snp.confidence}</Text>
                        )}
                        {snp.importanceScore && snp.importanceScore > 10 && (
                          <div style={{
                            backgroundColor: snp.importanceScore > 20 ? '#FFE5E5' : snp.importanceScore > 15 ? '#FFF5E5' : '#FFE',
                            color: snp.importanceScore > 20 ? '#C00' : snp.importanceScore > 15 ? '#C60' : '#990',
                            padding: '2px 8px',
                            borderRadius: '4px',
                            fontSize: '12px',
                            fontWeight: 500
                          }}>
                            High Importance
                          </div>
                        )}
                      </Stack>

                      {/* ClinVar Info */}
                      {snp.clinvarCondition && snp.clinvarCondition !== 'not provided' && (
                        <div style={{
                          backgroundColor: '#FFF9E5',
                          border: '1px solid #FFE5A0',
                          borderRadius: '6px',
                          padding: '8px 12px',
                          marginTop: '4px'
                        }}>
                          <Stack direction={Direction.Horizontal} shouldAddGutters={true} defaultGutter={PaddingSize.Default} childAlignment={Alignment.Center}>
                            <Text variant='note'>⚕️ ClinVar:</Text>
                            <Text variant='default'>{snp.clinvarCondition}</Text>
                          </Stack>
                        </div>
                      )}

                      {/* Sources */}
                      <Text variant='note' tag='em'>Sources: {snp.sources.join(', ')}</Text>
                    </Stack>
                  </div>
                ))}
              </Stack>
            </div>
          ))}
        </Stack>
      </div>

      {/* Footer Actions */}
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
