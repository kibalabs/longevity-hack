
import React from 'react';

import { Alignment, Direction, PaddingSize, Spacing, Stack, Text, TextAlignment } from '@kibalabs/ui-react';

export function HomePage(): React.ReactElement {
  return (
    <Stack direction={Direction.Vertical} childAlignment={Alignment.Center} contentAlignment={Alignment.Center} isFullHeight={true} isFullWidth={true} isScrollableVertically={true} paddingVertical={PaddingSize.Wide2} paddingHorizontal={PaddingSize.Wide2}>
      <Stack direction={Direction.Vertical} childAlignment={Alignment.Center} contentAlignment={Alignment.Center} shouldAddGutters={true} isFullHeight={true} maxWidth='600px'>
        <Text alignment={TextAlignment.Center} variant='header1'>Longevity Hack</Text>
        <Spacing variant={PaddingSize.Wide} />
        <Text alignment={TextAlignment.Center} variant='bold-large'>Coming Soon</Text>
        <Spacing variant={PaddingSize.Wide} />
        <Text alignment={TextAlignment.Center}>We&apos;re building something amazing. Stay tuned for updates!</Text>
      </Stack>
    </Stack>
  );
}
