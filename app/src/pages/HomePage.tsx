
import React from 'react';

import { useNavigator } from '@kibalabs/core-react';
import { Alignment, Box, Button, Checkbox, Direction, PaddingSize, Spacing, Stack, Text, TextAlignment } from '@kibalabs/ui-react';
import { Dropzone } from '@kibalabs/ui-react-dropzone';

import { useGlobals } from '../GlobalsContext';

export function HomePage(): React.ReactElement {
  const navigator = useNavigator();
  const { longevityClient } = useGlobals();
  const [hasCheckedConsent, setHasCheckedConsent] = React.useState(false);
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null);

  const onFileSelected = async (files: File[]): Promise<void> => {
    if (files.length > 0) {
      setSelectedFile(files[0]);
    }
  };

  const onContinueClick = async (): Promise<void> => {
    if (!hasCheckedConsent || !selectedFile) {
      return;
    }
    try {
      const analysis = await longevityClient.createGenomeAnalysis(selectedFile.name, selectedFile.type || 'text/plain');
      navigator.navigateTo(`/upload?id=${analysis.genomeAnalysisId}`);
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  const onSeeExampleClick = async (): Promise<void> => {
    try {
      const exampleId = await longevityClient.getExampleAnalysisId();
      navigator.navigateTo(`/upload?id=${exampleId}`);
    } catch (error) {
      console.error('Failed to load example:', error);
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
        <Button variant='primary' text='Continue' onClicked={onContinueClick} isEnabled={hasCheckedConsent && selectedFile !== null} />
        <Button variant='secondary' text='See an Example' onClicked={onSeeExampleClick} />
      </Stack>
    </Stack>
  );
}
