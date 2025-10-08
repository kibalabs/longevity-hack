import React from 'react';

import { getClassName, RecursivePartial } from '@kibalabs/core';
import { IMultiAnyChildProps } from '@kibalabs/core-react';
import { IBoxTheme, IComponentProps, themeToCss, ThemeType } from '@kibalabs/ui-react';
import { styled } from 'styled-components';

export interface ITableTheme extends ThemeType {
  background: IBoxTheme;
}

// NOTE(krishan711): table can't have border-radius if border-collapse: collapse is set
export const TableThemedStyle = (theme: RecursivePartial<ITableTheme>): string => `
  ${themeToCss(theme.background)};
`;

interface IStyledTableProps {
  $theme?: RecursivePartial<ITableTheme>;
}

export const StyledTable = styled.table<IStyledTableProps>`
  width: 100%;
  height: 100%;
  overflow: auto;
  border-collapse: separate;
  & > thead {
    border-collapse: collapse;
  }
  & > tbody {
    border-collapse: collapse;
  }

  && {
    ${(props: IStyledTableProps): string => (props.$theme ? TableThemedStyle(props.$theme) : '')};
  }
`;

export interface ITableProps extends IComponentProps<ITableTheme>, IMultiAnyChildProps {
}

export function Table({
  className = '',
  variant = 'default',
  ...props
}: ITableProps): React.ReactElement {
  return (
    <StyledTable
      id={props.id}
      className={getClassName(Table.displayName, className, ...(variant.split('-') || []))}
      $theme={props.theme}
    >
      {props.children}
    </StyledTable>
  );
}
Table.displayName = 'Table';
