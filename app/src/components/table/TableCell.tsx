import React from 'react';

import { getClassName, RecursivePartial } from '@kibalabs/core';
import { IMultiAnyChildProps } from '@kibalabs/core-react';
import { IBoxTheme, IComponentProps, ITextTheme, themeToCss, ThemeType } from '@kibalabs/ui-react';
import { styled } from 'styled-components';

export interface ITableCellThemeBase extends ThemeType {
  text: ITextTheme;
  background: IBoxTheme;
}

export interface ITableCellThemeState extends ThemeType {
  default: ITableCellThemeBase;
  hover: RecursivePartial<ITableCellThemeBase>;
  press: RecursivePartial<ITableCellThemeBase>;
  focus: RecursivePartial<ITableCellThemeBase>;
}

export interface ITableCellTheme extends ThemeType {
  normal: ITableCellThemeState;
  disabled: RecursivePartial<ITableCellThemeState>;
}

export const TableCellThemedStyle = (theme: RecursivePartial<ITableCellTheme>): string => `
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

export interface IStyledTableCellProps {
  $theme?: RecursivePartial<ITableCellTheme>;
}

export const StyledTableCell = styled.td<IStyledTableCellProps>`
  overflow: hidden;
  vertical-align: middle;
  white-space: nowrap;
  &.clickable {
    cursor: pointer;
  }

  && {
    ${(props: IStyledTableCellProps): string => (props.$theme ? TableCellThemedStyle(props.$theme) : '')};
  }
`;

export interface ITableCellProps extends IComponentProps<ITableCellTheme>, IMultiAnyChildProps {
  headerId?: string;
  onClicked?: (headerId: string) => void;
}

export function TableCell({
  className = '',
  variant = 'default',
  ...props
}: ITableCellProps): React.ReactElement {
  const onClicked = (): void => {
    if (props.onClicked && props.headerId) {
      props.onClicked(props.headerId);
    }
  };

  return (
    <StyledTableCell
      id={props.id}
      className={getClassName(TableCell.displayName, className, props.onClicked != null && 'clickable', ...(variant?.split('-') || []))}
      onClick={onClicked}
      $theme={props.theme}
    >
      {props.children}
    </StyledTableCell>
  );
}
TableCell.displayName = 'TableCell';
