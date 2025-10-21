
import React from 'react';

import { useNavigator } from '@kibalabs/core-react';
import { Alignment, Box, Button, Checkbox, Direction, PaddingSize, Spacing, Stack, Text, TextAlignment } from '@kibalabs/ui-react';
import { Dropzone } from '@kibalabs/ui-react-dropzone';

import { useGlobals } from '../GlobalsContext';
import { setPendingUpload } from '../util/fileUploadStore';

export function HomePage(): React.ReactElement {
  const navigator = useNavigator();
  const { longevityClient } = useGlobals();
  const [hasCheckedConsent, setHasCheckedConsent] = React.useState(false);
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);

  const onFileSelected = async (files: File[]): Promise<void> => {
    if (files.length > 0) {
      setSelectedFile(files[0]);
    }
  };

  const onContinueClick = async (): Promise<void> => {
    if (!hasCheckedConsent || !selectedFile) {
      return;
    }
    setErrorMessage(null);
    try {
      // Create the analysis first (status: waiting_for_upload)
      const analysis = await longevityClient.createGenomeAnalysis(selectedFile.name, selectedFile.type || 'text/plain');

      // Store the file reference in memory (no blocking!)
      setPendingUpload(analysis.genomeAnalysisId, selectedFile);

      // Navigate immediately - no waiting!
      navigator.navigateTo(`/upload?id=${analysis.genomeAnalysisId}`);
    } catch (error) {
      console.error('Failed to create analysis:', error);
      setErrorMessage('Failed to start analysis. Please try again.');
    }
  };

  const onSeeExampleClick = async (): Promise<void> => {
    setErrorMessage(null);
    try {
      const exampleId = await longevityClient.getExampleAnalysisId();
      navigator.navigateTo(`/results?id=${exampleId}`);
    } catch (error) {
      console.error('Failed to load example:', error);
      setErrorMessage('Failed to load example. Please try again.');
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      padding: '40px 24px',
    }}>
      {/* Hero Section */}
      <div style={{
        width: '100%',
        maxWidth: '900px',
        textAlign: 'center',
        marginBottom: '80px',
        marginTop: '60px',
      }}>
        {/* Logo above title */}
        <div style={{
          fontSize: '24px',
          fontWeight: 600,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          marginBottom: '8px',
          paddingBottom: '8px',
          letterSpacing: '0.5px',
        }}>
          GenomeAgent
        </div>

        <style>{`
          @keyframes gradientShift {
            0% {
              background-position: 0% 50%;
            }
            50% {
              background-position: 100% 50%;
            }
            100% {
              background-position: 0% 50%;
            }
          }
        `}</style>
        <h1 style={{
          fontSize: '56px',
          fontWeight: 700,
          margin: '0 0 24px 0',
          letterSpacing: '-1px',
          lineHeight: '1.2',
          paddingBottom: '8px',
          background: 'linear-gradient(90deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #667eea 75%, #764ba2 100%)',
          backgroundSize: '200% auto',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          animation: 'gradientShift 8s ease-in-out infinite',
          display: 'inline-block',
        }}>
          Understand your genome<br/>to unlock a longer and healthier life
        </h1>
        <p style={{
          fontSize: '20px',
          color: '#444',
          lineHeight: '1.6',
          maxWidth: '700px',
          margin: '0 auto 20px auto',
          fontWeight: 400,
        }}>
          AI agents analyze your genetic data to reveal personalized insights for living longer and healthier with science-backed recommendations.
          Stay updated as new research emerges that's relevant to your unique genome.
        </p>
      </div>

      {/* How It Works Section */}
      <div style={{
        width: '100%',
        maxWidth: '1100px',
        marginBottom: '80px',
      }}>
        <h2 style={{
          fontSize: '32px',
          fontWeight: 700,
          color: '#5568d3',
          textAlign: 'center',
          margin: '0 0 56px 0',
        }}>
          How It Works
        </h2>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '36px',
        }}>
          {/* Card 1 */}
          <div style={{
            position: 'relative',
            border: '2px solid rgba(102, 126, 234, 0.2)',
            borderRadius: '24px',
            background: 'linear-gradient(145deg, rgba(255, 255, 255, 0.55) 0%, rgba(252, 248, 255, 0.55) 100%)',
            backdropFilter: 'blur(20px)',
            padding: '40px 32px',
            boxShadow: '0 12px 40px rgba(102, 126, 234, 0.15), 0 4px 12px rgba(118, 75, 162, 0.08)',
            transition: 'transform 0.3s ease, box-shadow 0.3s ease',
            cursor: 'default',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-4px)';
            e.currentTarget.style.boxShadow = '0 16px 48px rgba(102, 126, 234, 0.2), 0 8px 16px rgba(118, 75, 162, 0.12)';
            e.currentTarget.style.background = 'linear-gradient(145deg, rgba(255, 255, 255, 0.95) 0%, rgba(252, 248, 255, 0.95) 100%)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '0 12px 40px rgba(102, 126, 234, 0.15), 0 4px 12px rgba(118, 75, 162, 0.08)';
            e.currentTarget.style.background = 'linear-gradient(145deg, rgba(255, 255, 255, 0.55) 0%, rgba(252, 248, 255, 0.55) 100%)';
          }}>
            <div style={{ fontSize: '56px', marginBottom: '40px', textAlign: 'center' }}>🧬</div>
            <h3 style={{ fontSize: '24px', fontWeight: 700, color: '#1a1a1a', marginBottom: '16px', textAlign: 'center' }}>
              Upload Your Genome
            </h3>
            <p style={{ fontSize: '16px', color: '#555', lineHeight: '1.7', margin: 0, textAlign: 'center' }}>
              Works with 23andMe, Ancestry DNA, and VCF files. Your data stays private and secure.
            </p>
          </div>

          {/* Card 2 */}
          <div style={{
            position: 'relative',
            border: '2px solid rgba(102, 126, 234, 0.2)',
            borderRadius: '24px',
            background: 'linear-gradient(145deg, rgba(255, 255, 255, 0.55) 0%, rgba(252, 248, 255, 0.55) 100%)',
            backdropFilter: 'blur(20px)',
            padding: '40px 32px',
            boxShadow: '0 12px 40px rgba(102, 126, 234, 0.15), 0 4px 12px rgba(118, 75, 162, 0.08)',
            transition: 'transform 0.3s ease, box-shadow 0.3s ease',
            cursor: 'default',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-4px)';
            e.currentTarget.style.boxShadow = '0 16px 48px rgba(102, 126, 234, 0.2), 0 8px 16px rgba(118, 75, 162, 0.12)';
            e.currentTarget.style.background = 'linear-gradient(145deg, rgba(255, 255, 255, 0.95) 0%, rgba(252, 248, 255, 0.95) 100%)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '0 12px 40px rgba(102, 126, 234, 0.15), 0 4px 12px rgba(118, 75, 162, 0.08)';
            e.currentTarget.style.background = 'linear-gradient(145deg, rgba(255, 255, 255, 0.55) 0%, rgba(252, 248, 255, 0.55) 100%)';
          }}>
            <div style={{ fontSize: '56px', marginBottom: '40px', textAlign: 'center' }}>🤖</div>
            <h3 style={{ fontSize: '24px', fontWeight: 700, color: '#1a1a1a', marginBottom: '16px', textAlign: 'center' }}>
              AI Agent Analysis
            </h3>
            <p style={{ fontSize: '16px', color: '#555', lineHeight: '1.7', margin: 0, textAlign: 'center' }}>
              Our AI agents analyze your variants focusing on longevity, healthspan, and disease prevention.
            </p>
          </div>

          {/* Card 3 */}
          <div style={{
            position: 'relative',
            border: '2px solid rgba(102, 126, 234, 0.2)',
            borderRadius: '24px',            background: 'linear-gradient(145deg, rgba(255, 255, 255, 0.55) 0%, rgba(252, 248, 255, 0.55) 100%)',
            backdropFilter: 'blur(20px)',
            padding: '40px 32px',
            boxShadow: '0 12px 40px rgba(102, 126, 234, 0.15), 0 4px 12px rgba(118, 75, 162, 0.08)',
            transition: 'transform 0.3s ease, box-shadow 0.3s ease',
            cursor: 'default',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-4px)';
            e.currentTarget.style.boxShadow = '0 16px 48px rgba(102, 126, 234, 0.2), 0 8px 16px rgba(118, 75, 162, 0.12)';
            e.currentTarget.style.background = 'linear-gradient(145deg, rgba(255, 255, 255, 0.95) 0%, rgba(252, 248, 255, 0.95) 100%)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '0 12px 40px rgba(102, 126, 234, 0.15), 0 4px 12px rgba(118, 75, 162, 0.08)';
            e.currentTarget.style.background = 'linear-gradient(145deg, rgba(255, 255, 255, 0.55) 0%, rgba(252, 248, 255, 0.55) 100%)';
          }}>
            <div style={{ fontSize: '56px', marginBottom: '40px', textAlign: 'center' }}>🔔</div>
            <h3 style={{ fontSize: '24px', fontWeight: 700, color: '#1a1a1a', marginBottom: '16px', textAlign: 'center' }}>
              Stay Updated
            </h3>
            <p style={{ fontSize: '16px', color: '#555', lineHeight: '1.7', margin: 0, textAlign: 'center' }}>
              Get notified when new research is published that's relevant to your genetic profile.
            </p>
          </div>
        </div>
      </div>

      {/* Upload Section */}
      <div style={{
        width: '100%',
        maxWidth: '680px',
        border: '2px solid rgba(102, 126, 234, 0.2)',
        borderRadius: '24px',
        background: 'linear-gradient(145deg, rgba(255, 255, 255, 0.95) 0%, rgba(252, 248, 255, 0.95) 100%)',
        backdropFilter: 'blur(20px)',
        padding: '48px 40px',
        boxShadow: '0 12px 40px rgba(102, 126, 234, 0.15), 0 4px 12px rgba(118, 75, 162, 0.08)',
      }}>
        <h2 style={{
          fontSize: '32px',
          fontWeight: 700,
          color: '#1a1a1a',
          textAlign: 'center',
          margin: '0 0 32px 0',
        }}>
          Get Started
        </h2>

        <div style={{ marginBottom: '32px' }}>
          <Dropzone onFilesChosen={onFileSelected}>
            <div style={{
              // border: '2px dashed rgba(102, 126, 234, 0.3)',
              borderRadius: '16px',
              padding: '48px 24px',
              textAlign: 'center',
              cursor: 'pointer',
              // background: selectedFile ? 'rgba(102, 126, 234, 0.04)' : 'transparent',
              transition: 'all 0.3s ease',
            }}>
              <div style={{ fontSize: '56px', marginBottom: '16px' }}>📤</div>
              <div style={{ fontSize: '17px', fontWeight: 600, color: '#1a1a1a', marginBottom: '8px' }}>
                {selectedFile ? `Selected: ${selectedFile.name}` : 'Drag your file here or click to browse'}
              </div>
              <div style={{ fontSize: '15px', color: '#555' }}>
                Supports 23andMe, Ancestry DNA, and VCF files
              </div>
            </div>
          </Dropzone>
        </div>

        <div style={{
          padding: '24px',
          marginBottom: '32px',
        }}>
          <div style={{ fontSize: '18px', fontWeight: 700, color: '#1a1a1a', marginBottom: '12px' }}>
            Privacy & Consent
          </div>
          <div style={{ fontSize: '15px', color: '#555', marginBottom: '16px', lineHeight: '1.7' }}>
            Your genetic data is stored securely and never shared with third parties. We only analyze the traits you select.
          </div>
          <label style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={hasCheckedConsent}
              onChange={(): void => setHasCheckedConsent(!hasCheckedConsent)}
              style={{ marginTop: '4px', cursor: 'pointer', accentColor: '#667eea', width: '18px', height: '18px' }}
            />
            <span style={{ fontSize: '15px', color: '#1a1a1a', lineHeight: '1.6' }}>
              I consent to the privacy policy and understand how my data will be used
            </span>
          </label>
        </div>

        {errorMessage && (
          <div style={{
            background: 'rgba(255, 59, 48, 0.08)',
            padding: '20px',
            borderRadius: '12px',
            border: '2px solid rgba(255, 59, 48, 0.2)',
            marginBottom: '32px',
          }}>
            <div style={{ fontWeight: 700, color: '#FF3B30', marginBottom: '6px', fontSize: '16px' }}>Error</div>
            <div style={{ fontSize: '15px', color: '#D32F2F', lineHeight: '1.5' }}>{errorMessage}</div>
          </div>
        )}

        <button
          onClick={onContinueClick}
          disabled={!hasCheckedConsent || !selectedFile}
          style={{
            width: '100%',
            background: (hasCheckedConsent && selectedFile)
              ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
              : 'rgba(0, 0, 0, 0.15)',
            color: 'white',
            border: 'none',
            borderRadius: '14px',
            padding: '18px',
            fontSize: '18px',
            fontWeight: 700,
            cursor: (hasCheckedConsent && selectedFile) ? 'pointer' : 'not-allowed',
            marginBottom: '16px',
            transition: 'all 0.3s ease',
            boxShadow: (hasCheckedConsent && selectedFile) ? '0 4px 16px rgba(102, 126, 234, 0.3)' : 'none',
          }}
          onMouseEnter={(e) => {
            if (hasCheckedConsent && selectedFile) {
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.4)';
            }
          }}
          onMouseLeave={(e) => {
            if (hasCheckedConsent && selectedFile) {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 4px 16px rgba(102, 126, 234, 0.3)';
            }
          }}
        >
          Continue
        </button>

        <button
          onClick={onSeeExampleClick}
          style={{
            width: '100%',
            background: 'transparent',
            color: '#667eea',
            border: '2px solid #667eea',
            borderRadius: '14px',
            padding: '16px',
            fontSize: '17px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.3s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(102, 126, 234, 0.08)';
            e.currentTarget.style.transform = 'translateY(-2px)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'transparent';
            e.currentTarget.style.transform = 'translateY(0)';
          }}
        >
          See an Example
        </button>
      </div>
    </div>
  );
}
