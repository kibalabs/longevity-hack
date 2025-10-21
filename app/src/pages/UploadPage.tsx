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
                group.category,
                group.categoryDescription,
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
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      width: '100%',
      padding: '40px 24px',
    }}>
      {!genomeAnalysisResults && genomeAnalysis && (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          width: '100%',
          maxWidth: '900px',
          gap: '48px',
        }}>
          {/* Step indicators */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '16px',
            width: '100%',
            flexWrap: 'wrap',
          }}>
            {ALL_STEPS.map((stepInfo: StepInfo, index: number): React.ReactElement => {
              const currentStep = getCurrentStepNumber(displayedStatus);
              const isActive = stepInfo.step === currentStep;
              const isCompleted = stepInfo.step < currentStep;

              return (
                <React.Fragment key={stepInfo.step}>
                  <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '8px',
                  }}>
                    <div
                      style={{
                        width: '56px',
                        height: '56px',
                        borderRadius: '50%',
                        background: isActive
                          ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                          : isCompleted
                            ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                            : 'rgba(0, 0, 0, 0.1)',
                        color: isActive || isCompleted ? 'white' : '#999',
                        fontWeight: isActive ? 700 : 600,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '20px',
                        border: isActive ? '3px solid rgba(102, 126, 234, 0.3)' : 'none',
                        boxShadow: isActive ? '0 4px 20px rgba(102, 126, 234, 0.4)' : isCompleted ? '0 2px 12px rgba(102, 126, 234, 0.2)' : 'none',
                        transition: 'all 0.3s ease',
                      }}
                    >
                      {isCompleted ? '✓' : stepInfo.step}
                    </div>
                    <span style={{
                      fontSize: '14px',
                      fontWeight: isActive ? 600 : 500,
                      color: isActive ? '#1a1a1a' : '#666',
                    }}>{stepInfo.label}</span>
                  </div>
                  {index < ALL_STEPS.length - 1 && (
                    <div
                      style={{
                        flex: 1,
                        height: '4px',
                        background: isCompleted
                          ? 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)'
                          : 'rgba(0, 0, 0, 0.1)',
                        marginTop: '-30px',
                        minWidth: '40px',
                        maxWidth: '80px',
                        borderRadius: '2px',
                        transition: 'all 0.3s ease',
                      }}
                    />
                  )}
                </React.Fragment>
              );
            })}
          </div>

          {/* Current step details */}
          {ALL_STEPS.map((stepInfo: StepInfo): React.ReactElement | null => {
            if (stepInfo.status !== displayedStatus) return null;

            return (
              <div key={stepInfo.status} style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '24px',
                width: '100%',
                maxWidth: '680px',
                border: '2px solid rgba(102, 126, 234, 0.2)',
                borderRadius: '24px',
                background: 'linear-gradient(145deg, rgba(255, 255, 255, 0.95) 0%, rgba(252, 248, 255, 0.95) 100%)',
                backdropFilter: 'blur(20px)',
                padding: '48px 40px',
                boxShadow: '0 12px 40px rgba(102, 126, 234, 0.15), 0 4px 12px rgba(118, 75, 162, 0.08)',
              }}>
                <div style={{ fontSize: '72px' }}>{stepInfo.icon}</div>
                <h2 style={{
                  fontSize: '32px',
                  fontWeight: 700,
                  color: '#1a1a1a',
                  margin: 0,
                  textAlign: 'center',
                }}>{stepInfo.title}</h2>
                <p style={{
                  fontSize: '16px',
                  color: '#555',
                  lineHeight: '1.7',
                  textAlign: 'center',
                  margin: 0,
                  maxWidth: '520px',
                }}>{stepInfo.description}</p>

                <div style={{ width: '100%', height: '24px' }} />

                <div
                  style={{
                    width: '100%',
                    maxWidth: '520px',
                    height: '10px',
                    background: 'rgba(0, 0, 0, 0.08)',
                    borderRadius: '5px',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      width: `${(getCurrentStepNumber(displayedStatus) / ALL_STEPS.length) * 100}%`,
                      height: '100%',
                      background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
                      transition: 'width 0.5s ease-in-out',
                      borderRadius: '5px',
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {errorMessage && (
        <div style={{
          width: '100%',
          maxWidth: '680px',
          border: '2px solid rgba(255, 59, 48, 0.2)',
          borderRadius: '24px',
          background: 'rgba(255, 59, 48, 0.08)',
          padding: '32px',
        }}>
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
          }}>
            <div style={{
              fontSize: '18px',
              fontWeight: 700,
              color: '#FF3B30',
            }}>Error</div>
            <p style={{
              fontSize: '16px',
              color: '#D32F2F',
              lineHeight: '1.6',
              margin: 0,
            }}>{errorMessage}</p>
            <div style={{ height: '8px' }} />
            <button
              onClick={(): void => navigator.navigateTo('/')}
              style={{
                padding: '12px 28px',
                background: 'transparent',
                color: '#667eea',
                border: '2px solid #667eea',
                borderRadius: '12px',
                fontSize: '15px',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.3s ease',
              }}
              onMouseEnter={(e): void => {
                e.currentTarget.style.background = 'rgba(102, 126, 234, 0.08)';
              }}
              onMouseLeave={(e): void => {
                e.currentTarget.style.background = 'transparent';
              }}
            >
              Go Back
            </button>
          </div>
        </div>
      )}

      {genomeAnalysis?.status === 'failed' && (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '24px',
          width: '100%',
          maxWidth: '680px',
          border: '2px solid rgba(102, 126, 234, 0.2)',
          borderRadius: '24px',
          background: 'linear-gradient(145deg, rgba(255, 255, 255, 0.95) 0%, rgba(252, 248, 255, 0.95) 100%)',
          backdropFilter: 'blur(20px)',
          padding: '48px 40px',
          boxShadow: '0 12px 40px rgba(102, 126, 234, 0.15), 0 4px 12px rgba(118, 75, 162, 0.08)',
        }}>
          <div style={{ fontSize: '64px' }}>❌</div>
          <h3 style={{
            fontSize: '28px',
            fontWeight: 700,
            color: '#1a1a1a',
            margin: 0,
          }}>Analysis Failed</h3>
          <p style={{
            fontSize: '16px',
            color: '#555',
            lineHeight: '1.7',
            textAlign: 'center',
            margin: 0,
          }}>An error occurred during analysis</p>
          <div style={{ height: '16px' }} />
          <button
            onClick={(): void => window.location.reload()}
            style={{
              padding: '14px 36px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '12px',
              fontSize: '16px',
              fontWeight: 700,
              cursor: 'pointer',
              boxShadow: '0 4px 16px rgba(102, 126, 234, 0.3)',
              transition: 'all 0.3s ease',
            }}
            onMouseEnter={(e): void => {
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.4)';
            }}
            onMouseLeave={(e): void => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 4px 16px rgba(102, 126, 234, 0.3)';
            }}
          >
            Try Again
          </button>
        </div>
      )}

      {genomeAnalysisResults && genomeAnalysis && displayedStatus === 'completed' && (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          width: '100%',
          maxWidth: '900px',
          gap: '48px',
        }}>
          {/* Step indicators - all complete */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '16px',
            width: '100%',
            flexWrap: 'wrap',
          }}>
            {ALL_STEPS.map((stepInfo: StepInfo, index: number): React.ReactElement => (
              <React.Fragment key={stepInfo.step}>
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '8px',
                }}>
                  <div
                    style={{
                      width: '56px',
                      height: '56px',
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      color: 'white',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '20px',
                      boxShadow: '0 2px 12px rgba(102, 126, 234, 0.2)',
                    }}
                  >
                    ✓
                  </div>
                  <span style={{
                    fontSize: '14px',
                    fontWeight: 500,
                    color: '#666',
                  }}>{stepInfo.label}</span>
                </div>
                {index < ALL_STEPS.length - 1 && (
                  <div
                    style={{
                      flex: 1,
                      height: '4px',
                      background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
                      marginTop: '-30px',
                      minWidth: '40px',
                      maxWidth: '80px',
                      borderRadius: '2px',
                    }}
                  />
                )}
              </React.Fragment>
            ))}
          </div>

          {/* Summary */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '24px',
            width: '100%',
            maxWidth: '680px',
          }}>
            <div style={{ fontSize: '72px' }}>🎉</div>
            <h2 style={{
              fontSize: '36px',
              fontWeight: 700,
              color: '#1a1a1a',
              margin: 0,
              textAlign: 'center',
            }}>Analysis Complete!</h2>
            <p style={{
              fontSize: '17px',
              color: '#555',
              margin: 0,
              fontWeight: 500,
            }}>{genomeAnalysis.fileName}</p>
            {genomeAnalysis.detectedFormat && (
              <p style={{
                fontSize: '15px',
                color: '#888',
                margin: 0,
              }}>Detected format: {genomeAnalysis.detectedFormat}</p>
            )}

            <div style={{ height: '16px' }} />

            <div
              style={{
                width: '100%',
                border: '2px solid rgba(102, 126, 234, 0.2)',
                borderRadius: '24px',
                background: 'linear-gradient(145deg, rgba(255, 255, 255, 0.95) 0%, rgba(252, 248, 255, 0.95) 100%)',
                backdropFilter: 'blur(20px)',
                padding: '40px',
                boxShadow: '0 12px 40px rgba(102, 126, 234, 0.15), 0 4px 12px rgba(118, 75, 162, 0.08)',
              }}
            >
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '24px',
              }}>
                <h3 style={{
                  fontSize: '24px',
                  fontWeight: 700,
                  color: '#1a1a1a',
                  margin: 0,
                  textAlign: 'center',
                }}>Results Summary</h3>
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '16px',
                }}>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    gap: '12px',
                  }}>
                    <span style={{
                      fontSize: '16px',
                      fontWeight: 700,
                      color: '#1a1a1a',
                    }}>Trait Groups Analyzed:</span>
                    <span style={{
                      fontSize: '16px',
                      color: '#555',
                    }}>{genomeAnalysisResults.length}</span>
                  </div>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    gap: '12px',
                  }}>
                    <span style={{
                      fontSize: '16px',
                      fontWeight: 700,
                      color: '#1a1a1a',
                    }}>Total SNPs Identified:</span>
                    <span style={{
                      fontSize: '16px',
                      color: '#555',
                    }}>{genomeAnalysisResults.reduce((sum: number, r: Resources.GenomeAnalysisResult): number => sum + r.snps.length, 0)}</span>
                  </div>
                </div>
                <div style={{ height: '8px' }} />
                <p style={{
                  fontSize: '15px',
                  color: '#888',
                  textAlign: 'center',
                  margin: 0,
                  lineHeight: '1.6',
                }}>Your personalized genetic insights are ready to explore</p>
              </div>
            </div>
          </div>

          <div style={{ height: '16px' }} />

          <button
            onClick={(): void => navigator.navigateTo(`/results?id=${genomeAnalysisId}`)}
            style={{
              padding: '16px 48px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '14px',
              fontSize: '18px',
              fontWeight: 700,
              cursor: 'pointer',
              boxShadow: '0 4px 16px rgba(102, 126, 234, 0.3)',
              transition: 'all 0.3s ease',
            }}
            onMouseEnter={(e): void => {
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.4)';
            }}
            onMouseLeave={(e): void => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 4px 16px rgba(102, 126, 234, 0.3)';
            }}
          >
            View Results →
          </button>
        </div>
      )}
    </div>
  );
}
