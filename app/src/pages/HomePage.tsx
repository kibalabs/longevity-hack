
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
    <Stack isScrollableVertically={true} childAlignment={Alignment.Center}>
      <Stack direction={Direction.Vertical} isFullWidth={true} shouldAddGutters={true} paddingHorizontal={PaddingSize.Wide2} paddingVertical={PaddingSize.Wide2} maxWidth='600px'>
        <Stack direction={Direction.Vertical} childAlignment={Alignment.Center} shouldAddGutters={true} defaultGutter={PaddingSize.Wide} isFullWidth={true}>
          <Text variant='header2' alignment={TextAlignment.Center}>Upload Your Genome</Text>
          <Text variant='default' alignment={TextAlignment.Center}>Drag and drop your raw DNA file from 23andMe, Ancestry, or VCF format</Text>
          <Spacing variant={PaddingSize.Wide} />
          <Dropzone onFilesChosen={onFileSelected}>
            <Box variant='default' isFullWidth={true}>
              <Stack direction={Direction.Vertical} childAlignment={Alignment.Center} contentAlignment={Alignment.Center} shouldAddGutters={true} defaultGutter={PaddingSize.Default} paddingVertical={PaddingSize.Wide3} paddingHorizontal={PaddingSize.Wide2}>
                <Text variant='header1'>📤</Text>
                <Text variant='default' alignment={TextAlignment.Center}>{selectedFile ? `Selected: ${selectedFile.name}` : 'Drag your file here or click to browse'}</Text>
                <Text variant='note' alignment={TextAlignment.Center}>Supports 23andMe, Ancestry DNA, and VCF files</Text>
              </Stack>
            </Box>
          </Dropzone>
          <Box variant='default' isFullWidth={true} maxWidth='600px'>
            <Stack direction={Direction.Vertical} shouldAddGutters={true} defaultGutter={PaddingSize.Default} paddingHorizontal={PaddingSize.Wide2} paddingVertical={PaddingSize.Wide2}>
              <Text variant='bold'>Privacy & Consent</Text>
              <Text variant='default'>Your genetic data is stored securely and never shared with third parties. We only analyze the traits you select.</Text>
              <Spacing variant={PaddingSize.Default} />
              <Checkbox
                text='I consent to the privacy policy and understand how my data will be used'
                isChecked={hasCheckedConsent}
                onToggled={(): void => setHasCheckedConsent(!hasCheckedConsent)}
              />
            </Stack>
          </Box>
        </Stack>
        {errorMessage && (
          <div style={{ maxWidth: '600px', width: '100%', backgroundColor: '#FFE5E5', padding: '16px', borderRadius: '8px', border: '1px solid #FF3B30' }}>
            <Stack direction={Direction.Vertical} shouldAddGutters={true} defaultGutter={PaddingSize.Default}>
              <div style={{ color: '#FF3B30' }}>
                <Text variant='bold'>Error</Text>
              </div>
              <Text variant='default'>{errorMessage}</Text>
            </Stack>
          </div>
        )}
        <Button variant='primary' text='Continue' onClicked={onContinueClick} isEnabled={hasCheckedConsent && selectedFile !== null} />
        <Button variant='secondary' text='See an Example' onClicked={onSeeExampleClick} />
      </Stack>
    </Stack>
  );
}
