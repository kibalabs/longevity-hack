import React from 'react';

import { getClassName, RecursivePartial } from '@kibalabs/core';
import { IMultiAnyChildProps } from '@kibalabs/core-react';
import { IBoxTheme, IComponentProps, ITextTheme, themeToCss, ThemeType } from '@kibalabs/ui-react';
import { styled } from 'styled-components';

export interface ITableRowThemeBase extends ThemeType {
  text: ITextTheme;
  background: IBoxTheme;
}

export interface ITableRowThemeState extends ThemeType {
  default: ITableRowThemeBase;
  hover: RecursivePartial<ITableRowThemeBase>;
  press: RecursivePartial<ITableRowThemeBase>;
  focus: RecursivePartial<ITableRowThemeBase>;
}

export interface ITableRowTheme extends ThemeType {
  normal: ITableRowThemeState;
  disabled: RecursivePartial<ITableRowThemeState>;
}

export const TableRowThemedStyle = (theme: RecursivePartial<ITableRowTheme>): string => `
  ${themeToCss(theme.normal?.default?.text)};
  ${themeToCss(theme.normal?.default?.background)};

  &.clickable {
    &:hover {
      ${themeToCss(theme.normal?.hover?.text)};
      ${themeToCss(theme.normal?.hover?.background)};
    }
    &:active {
      ${themeToCss(theme.normal?.press?.text)};
      ${themeToCss(theme.normal?.press?.background)};
    }
    &:focus {
      ${themeToCss(theme.normal?.focus?.text)};
      ${themeToCss(theme.normal?.focus?.background)};
    }
  }
`;

export interface IStyledTableRowProps {
  $theme?: RecursivePartial<ITableRowTheme>;
}

export const StyledTableRow = styled.tr<IStyledTableRowProps>`
  overflow: hidden;
  && {
    ${(props: IStyledTableRowProps): string => (props.$theme ? TableRowThemedStyle(props.$theme) : '')};
  }
`;

export interface ITableRowProps extends IComponentProps<ITableRowTheme>, IMultiAnyChildProps {
}

export function TableRow({
  className = '',
  variant = 'default',
  ...props
}: ITableRowProps): React.ReactElement {
  return (
    <StyledTableRow
      id={props.id}
      className={getClassName(TableRow.displayName, className, ...(variant?.split('-') || []))}
      $theme={props.theme}
    >
      {props.children}
    </StyledTableRow>
  );
}
TableRow.displayName = 'TableRow';
