import React from 'react';

import { useNavigator } from '@kibalabs/core-react';
import { Alignment, Button, Direction, PaddingSize, Spacing, Stack, Text, TextAlignment } from '@kibalabs/ui-react';

import * as Resources from '../client/resources';
import { useGlobals } from '../GlobalsContext';
import { clearPendingUpload, getPendingUpload } from '../util/fileUploadStore';

interface StepInfo {
  step: number;
  status: string;
  label: string;
  title: string;
  description: string;
  icon: string;
}

const ALL_STEPS: StepInfo[] = [
  {
    step: 1,
    status: 'waiting_for_upload',
    label: 'Preparing',
    title: 'Preparing upload...',
    description: 'Setting up your secure genome analysis workspace.',
    icon: '🔄',
  },
  {
    step: 2,
    status: 'uploading',
    label: 'Uploading',
    title: 'Uploading your genome...',
    description: 'Uploading your genome file securely to our servers.',
    icon: '📤',
  },
  {
    step: 3,
    status: 'validating',
    label: 'Validating',
    title: 'Validating your file...',
    description: "We're validating your DNA file to ensure it's in a supported format and contains the necessary data.",
    icon: '🧐',
  },
  {
    step: 4,
    status: 'parsing',
    label: 'Parsing',
    title: 'Parsing genetic data...',
    description: 'Parsing your genetic data and identifying relevant SNPs for analysis.',
    icon: '🔬',
  },
  {
    step: 5,
    status: 'building_baseline',
    label: 'Building Baseline',
    title: 'Building your baseline...',
    description: 'Building your genetic baseline and preparing trait insights. This helps us understand your unique genetic profile.',
    icon: '🛠️',
  },
  {
    step: 6,
    status: 'completed',
    label: 'Complete',
    title: 'Analysis Complete!',
    description: 'Your genetic analysis is ready to view.',
    icon: '🎉',
  },
];

const getCurrentStepNumber = (status: string): number => {
  const stepInfo = ALL_STEPS.find((s: StepInfo): boolean => s.status === status);
  return stepInfo ? stepInfo.step : 1;
};

export function UploadPage(): React.ReactElement {
  const navigator = useNavigator();
  const { longevityClient } = useGlobals();
  const [genomeAnalysisId, setGenomeAnalysisId] = React.useState<string | null>(null);
  const [genomeAnalysis, setGenomeAnalysis] = React.useState<Resources.GenomeAnalysis | null>(null);
  const [genomeAnalysisResults, setGenomeAnalysisResults] = React.useState<Resources.GenomeAnalysisResult[] | null>(null);
  const [displayedStatus, setDisplayedStatus] = React.useState<string>('waiting_for_upload');
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);
  const stepStartTimeRef = React.useRef<number>(Date.now());

  React.useEffect((): void => {
    // Get the analysis ID from URL query parameter
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get('id');

    if (id) {
      setGenomeAnalysisId(id);
      longevityClient.getGenomeAnalysis(id).then((analysis: Resources.GenomeAnalysis): void => {
        setGenomeAnalysis(analysis);

        // If we're waiting for upload, trigger it now
        if (analysis.status === 'waiting_for_upload') {
          // Retrieve file from in-memory store
          const file = getPendingUpload(id);

          if (file) {
            // Trigger upload immediately
            longevityClient.uploadGenomeFile(id, file).then((): void => {
              console.log('Upload completed');
              // Clean up the pending upload
              clearPendingUpload(id);
            }).catch((error: Error): void => {
              console.error('Upload failed:', error);
              setErrorMessage('Failed to upload file. Please try again.');
            });
          } else {
            console.warn('No pending file found for analysis:', id);
            setErrorMessage('No file found for upload. Please start over.');
          }
        }
      }).catch((error: Error): void => {
        console.error('Failed to fetch analysis:', error);
        setErrorMessage('Failed to load analysis. Please try again.');
      });
    } else {
      navigator.navigateTo('/');
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty array - only run once on mount

  React.useEffect((): (() => void) | void => {
    if (!genomeAnalysisId) return undefined;

    // Poll for status updates every 2 seconds
    const intervalId = setInterval((): void => {
      longevityClient.getGenomeAnalysis(genomeAnalysisId).then((analysis: Resources.GenomeAnalysis): void => {
        setGenomeAnalysis(analysis);

        // Load results when analysis is complete
        if (analysis.status === 'completed') {
          longevityClient.getGenomeAnalysisOverview(genomeAnalysisId).then((overview: Resources.GenomeAnalysisOverview): void => {
            setGenomeAnalysisResults(overview.categoryGroups.map((group): Resources.GenomeAnalysisResult => {
              return new Resources.GenomeAnalysisResult(
                group.genomeAnalysisResultId,
                genomeAnalysisId,
                group.phenotypeGroup,
                group.phenotypeDescription,
                group.topSnps,
              );
            }));
            // Immediately set displayedStatus to 'completed' to avoid blank screen
            setDisplayedStatus('completed');
            // Stop polling by clearing the interval
            clearInterval(intervalId);
          }).catch((error: Error): void => {
            console.error('Failed to fetch results:', error);
          });
        }
      }).catch((error: Error): void => {
        console.error('Failed to check analysis status:', error);
      });
    }, 2000);

    return (): void => {
      clearInterval(intervalId);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [genomeAnalysisId]); // Only depend on genomeAnalysisId

  // Separate effect to handle step transitions with minimum duration
  React.useEffect((): (() => void) | void => {
    if (!genomeAnalysis) return undefined;

    const currentStepNumber = getCurrentStepNumber(displayedStatus);
    const backendStepNumber = getCurrentStepNumber(genomeAnalysis.status);

    // If we're already at or past the backend step, no need to transition
    if (currentStepNumber >= backendStepNumber) return undefined;

    // We need to advance to the next step
    const nextStepNumber = currentStepNumber + 1;
    const nextStep = ALL_STEPS.find((s: StepInfo): boolean => s.step === nextStepNumber);
    if (!nextStep) return undefined;

    const elapsedTime = Date.now() - stepStartTimeRef.current;
    const MIN_STEP_DURATION = 5000; // 5 seconds
    const remainingTime = Math.max(0, MIN_STEP_DURATION - elapsedTime);

    // Schedule the transition to the next step
    const timeoutId = setTimeout((): void => {
      setDisplayedStatus(nextStep.status);
      stepStartTimeRef.current = Date.now();
    }, remainingTime);

    return (): void => clearTimeout(timeoutId);
  }, [genomeAnalysis, displayedStatus]);

  return (
    <Stack direction={Direction.Vertical} isFullWidth={true} isFullHeight={true} childAlignment={Alignment.Center} contentAlignment={Alignment.Center} shouldAddGutters={true} defaultGutter={PaddingSize.Wide2}>
      {!genomeAnalysisResults && genomeAnalysis && (
        <Stack direction={Direction.Vertical} shouldAddGutters={true} childAlignment={Alignment.Center} contentAlignment={Alignment.Center} defaultGutter={PaddingSize.Wide2} isFullWidth={true} paddingHorizontal={PaddingSize.Wide2} paddingVertical={PaddingSize.Wide2}>
          {/* Step indicators */}
          <Stack direction={Direction.Horizontal} shouldAddGutters={true} childAlignment={Alignment.Center} contentAlignment={Alignment.Center} defaultGutter={PaddingSize.Wide}>
            {ALL_STEPS.map((stepInfo: StepInfo, index: number): React.ReactElement => {
              const currentStep = getCurrentStepNumber(displayedStatus);
              const isActive = stepInfo.step === currentStep;
              const isCompleted = stepInfo.step < currentStep;

              return (
                <React.Fragment key={stepInfo.step}>
                  <Stack direction={Direction.Vertical} shouldAddGutters={true} childAlignment={Alignment.Center} defaultGutter={PaddingSize.Narrow}>
                    <div
                      style={{
                        width: '48px',
                        height: '48px',
                        borderRadius: '50%',
                        backgroundColor: isActive ? '#007AFF' : isCompleted ? '#007AFF' : '#E5E5E5',
                        color: isActive || isCompleted ? 'white' : '#8E8E93',
                        fontWeight: isActive ? 'bold' : 'normal',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '18px',
                        border: isActive ? '3px solid #007AFF' : 'none',
                      }}
                    >
                      {isCompleted ? '✓' : stepInfo.step}
                    </div>
                    <Text variant={isActive ? 'bold' : 'note'}>{stepInfo.label}</Text>
                  </Stack>
                  {index < ALL_STEPS.length - 1 && (
                    <div
                      style={{
                        flex: 1,
                        height: '3px',
                        backgroundColor: isCompleted ? '#007AFF' : '#E5E5E5',
                        marginTop: '-30px',
                        minWidth: '40px',
                        maxWidth: '120px',
                      }}
                    />
                  )}
                </React.Fragment>
              );
            })}
          </Stack>

          <Spacing variant={PaddingSize.Wide2} />

          {/* Current step details */}
          {ALL_STEPS.map((stepInfo: StepInfo): React.ReactElement | null => {
            if (stepInfo.status !== displayedStatus) return null;

            return (
              <Stack key={stepInfo.status} direction={Direction.Vertical} shouldAddGutters={true} childAlignment={Alignment.Center} contentAlignment={Alignment.Center} defaultGutter={PaddingSize.Wide}>
                <div style={{ fontSize: '64px' }}>{stepInfo.icon}</div>
                <Text variant='header2'>{stepInfo.title}</Text>
                <div style={{ maxWidth: '600px', textAlign: 'center' }}>
                  <Text variant='default'>{stepInfo.description}</Text>
                </div>
                <Spacing variant={PaddingSize.Wide} />
                <div
                  style={{
                    width: '100%',
                    maxWidth: '600px',
                    height: '8px',
                    backgroundColor: '#E5E5E5',
                    borderRadius: '4px',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      width: `${(getCurrentStepNumber(displayedStatus) / ALL_STEPS.length) * 100}%`,
                      height: '100%',
                      backgroundColor: '#007AFF',
                      transition: 'width 0.5s ease-in-out',
                    }}
                  />
                </div>
              </Stack>
            );
          })}
        </Stack>
      )}

      {errorMessage && (
        <Stack direction={Direction.Vertical} shouldAddGutters={true} childAlignment={Alignment.Center} contentAlignment={Alignment.Center} isFullWidth={true} paddingHorizontal={PaddingSize.Wide2}>
          <div style={{ maxWidth: '600px', width: '100%', backgroundColor: '#FFE5E5', padding: '16px', borderRadius: '8px', border: '1px solid #FF3B30' }}>
            <Stack direction={Direction.Vertical} shouldAddGutters={true} defaultGutter={PaddingSize.Default}>
              <div style={{ color: '#FF3B30' }}>
                <Text variant='bold'>Error</Text>
              </div>
              <Text variant='default'>{errorMessage}</Text>
              <Spacing variant={PaddingSize.Default} />
              <Button variant='secondary' text='Go Back' onClicked={(): void => navigator.navigateTo('/')} />
            </Stack>
          </div>
        </Stack>
      )}

      {genomeAnalysis?.status === 'failed' && (
        <Stack direction={Direction.Vertical} shouldAddGutters={true} childAlignment={Alignment.Center} contentAlignment={Alignment.Center}>
          <Text variant='header3'>Analysis Failed</Text>
          <Text variant='default'>An error occurred during analysis</Text>
          <Spacing variant={PaddingSize.Wide} />
          <Button variant='primary' text='Try Again' onClicked={(): void => window.location.reload()} />
        </Stack>
      )}

      {genomeAnalysisResults && genomeAnalysis && displayedStatus === 'completed' && (
        <Stack direction={Direction.Vertical} shouldAddGutters={true} childAlignment={Alignment.Center} contentAlignment={Alignment.Center} defaultGutter={PaddingSize.Wide2} isFullWidth={true} paddingHorizontal={PaddingSize.Wide2} paddingVertical={PaddingSize.Wide2}>
          {/* Step indicators - all complete */}
          <Stack direction={Direction.Horizontal} shouldAddGutters={true} childAlignment={Alignment.Center} contentAlignment={Alignment.Center} defaultGutter={PaddingSize.Wide}>
            {ALL_STEPS.map((stepInfo: StepInfo, index: number): React.ReactElement => (
              <React.Fragment key={stepInfo.step}>
                <Stack direction={Direction.Vertical} shouldAddGutters={true} childAlignment={Alignment.Center} defaultGutter={PaddingSize.Narrow}>
                  <div
                    style={{
                      width: '48px',
                      height: '48px',
                      borderRadius: '50%',
                      backgroundColor: '#007AFF',
                      color: 'white',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '18px',
                    }}
                  >
                    ✓
                  </div>
                  <Text variant='note'>{stepInfo.label}</Text>
                </Stack>
                {index < ALL_STEPS.length - 1 && (
                  <div
                    style={{
                      flex: 1,
                      height: '3px',
                      backgroundColor: '#007AFF',
                      marginTop: '-30px',
                      minWidth: '40px',
                      maxWidth: '120px',
                    }}
                  />
                )}
              </React.Fragment>
            ))}
          </Stack>

          <Spacing variant={PaddingSize.Wide2} />

          {/* Summary */}
          <Stack direction={Direction.Vertical} shouldAddGutters={true} childAlignment={Alignment.Center} contentAlignment={Alignment.Center} defaultGutter={PaddingSize.Wide}>
            <div style={{ fontSize: '64px' }}>🎉</div>
            <Text variant='header2'>Analysis Complete!</Text>
            <Text variant='default'>{genomeAnalysis.fileName}</Text>
            {genomeAnalysis.detectedFormat && (
              <Text variant='note'>Detected format: {genomeAnalysis.detectedFormat}</Text>
            )}

            <Spacing variant={PaddingSize.Wide} />

            <div
              style={{
                maxWidth: '600px',
                width: '100%',
                backgroundColor: '#F9F9F9',
                borderRadius: '12px',
                border: '1px solid #E5E5E5',
                padding: '24px',
              }}
            >
              <Stack direction={Direction.Vertical} shouldAddGutters={true} defaultGutter={PaddingSize.Wide}>
                <Text variant='header3' alignment={TextAlignment.Center}>Results Summary</Text>
                <Stack direction={Direction.Vertical} shouldAddGutters={true} defaultGutter={PaddingSize.Default}>
                  <Stack direction={Direction.Horizontal} contentAlignment={Alignment.Center} shouldAddGutters={true} defaultGutter={PaddingSize.Default}>
                    <Text variant='bold'>Trait Groups Analyzed:</Text>
                    <Text variant='default'>{genomeAnalysisResults.length}</Text>
                  </Stack>
                  <Stack direction={Direction.Horizontal} contentAlignment={Alignment.Center} shouldAddGutters={true} defaultGutter={PaddingSize.Default}>
                    <Text variant='bold'>Total SNPs Identified:</Text>
                    <Text variant='default'>{genomeAnalysisResults.reduce((sum: number, r: Resources.GenomeAnalysisResult): number => sum + r.snps.length, 0)}</Text>
                  </Stack>
                </Stack>
                <Spacing variant={PaddingSize.Default} />
                <Text variant='note' alignment={TextAlignment.Center}>Your personalized genetic insights are ready to explore</Text>
              </Stack>
            </div>
          </Stack>

          <Spacing variant={PaddingSize.Wide2} />

          <Button variant='primary' text='View Results →' onClicked={(): void => navigator.navigateTo(`/results?id=${genomeAnalysisId}`)} />
        </Stack>
      )}
    </Stack>
  );
}
