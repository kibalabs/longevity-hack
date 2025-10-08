import { buildTheme, ICheckboxTheme, ITextTheme, ITheme, mergeTheme, mergeThemePartial, ThemeMap } from '@kibalabs/ui-react';
import { buildToastThemes } from '@kibalabs/ui-react-toast';

export const buildYieldseekerTheme = (): ITheme => {
  const baseTheme = buildTheme();
  const textThemes: ThemeMap<ITextTheme> = {
    ...baseTheme.texts,
    default: mergeTheme(baseTheme.texts.default, {
      'font-family': '"IBM Plex Mono", monospace, sans-serif',
      'font-weight': '400',
    }),
    header1: {
      'font-weight': '800',
      color: '$colors.brandPrimary',
    },
    navBarLogo: {
      'font-weight': '800',
      color: 'white',
    },
    note: {
      color: '$colors.textClear20',
    },
    light: {
      color: '$colors.backgroundDarker50',
    },
    warning: {
      color: '$colors.warning',
    },
    header3: {
      'font-size': '1em',
      'font-weight': 'bolder',
    },
    header4: {
      'font-size': '1em',
      'font-weight': 'normal',
      'text-decoration': 'underline',
    },
    large: {
      'font-size': '1.25em',
    },
    larger: {
      'font-size': '2em',
    },
    passive: {
      opacity: '0.5',
    },
  };
  const theme = buildTheme({
    colors: {
      background: '#000',
      brandPrimary: '#27ec6fff',
      success: 'rgb(39, 236, 111)',
      warning: '#cf9f04',
    },
    dimensions: {
      borderRadius: '0.2em',
    },
    fonts: {
      main: {
        url: 'https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;1,100;1,200;1,300;1,400;1,500;1,600;1,700&display=swap',
      },
    },
    texts: textThemes,
    dividers: {
      light: {
        color: 'var(--color-background-light25)',
      },
      extraLight: {
        color: 'var(--color-background-light50)',
      },
    },
    buttons: {
      medium: {
        normal: {
          default: {
            background: {
              padding: `${baseTheme.dimensions.paddingWide} ${baseTheme.dimensions.paddingWide2}`,
            },
          },
        },
      },
      navBarLocation: {
        normal: {
          default: {
            text: {
              color: '$colors.text',
            },
          },
        },
      },
      destructive: {
        normal: {
          default: {
            background: {
              'background-color': '$colors.error',
            },
            text: {
              color: '$colors.error',
            },
          },
        },
      },
      destructivePassive: {
        normal: {
          default: {
            background: {
              'background-color': 'transparent',
            },
            text: {
              color: '$colors.error',
            },
          },
          hover: {
            background: {
              'background-color': '$colors.errorClear95',
            },
          },
          press: {
            background: {
              'background-color': '$colors.errorClear90',
            },
          },
        },
      },
      secondary: {
        normal: {
          default: {
            background: {
              'border-width': '1px',
            },
          },
        },
        disabled: {
          default: {
            background: {
              'background-color': 'transparent',
              'border-color': '$colors.textClear50',
            },
            text: {
              color: '$colors.textClear50',
            },
          },
        },
      },
      tertiary: {
        disabled: {
          default: {
            background: {
              'background-color': 'transparent',
            },
            text: {
              color: '$colors.textClear50',
            },
          },
        },
      },
      passive: {
        normal: {
          default: {
            text: {
              color: '$colors.text',
            },
          },
        },
      },
      veryPassive: {
        normal: {
          default: {
            text: {
              color: '$colors.textClear25',
            },
          },
        },
      },
      chatSuggestion: {
        normal: {
          default: {
            background: {
              'background-color': '$colors.backgroundLight05',
              'border-color': '$colors.backgroundLight25',
              'border-radius': '0.99em 0.99em 0 0.99em',
              'border-width': '1px',
              'border-style': 'dashed',
              'align-self': 'flex-end',
            },
            text: {
              'font-weight': 'normal',
              color: '$colors.text',
              'text-align': 'start',
            },
          },
          hover: {
            background: {
              'border-color': '$colors.brandPrimary',
              'border-style': 'solid',
            },
            text: {
              color: '$colors.brandPrimary',
            },
          },
        },
      },
      chatMenu: {
        normal: {
          default: {
            background: {
              'border-width': '0',
              padding: `${baseTheme.dimensions.paddingWide} ${baseTheme.dimensions.paddingWide}`,
            },
            text: {
              'font-weight': 'normal',
              color: '$colors.text',
            },
          },
        },
      },
      sidebar: {
        normal: {
          default: {
            background: {
              'border-color': '$colors.backgroundLight25',
              'border-style': 'solid',
              'border-width': '0 0 1px 0',
              'border-radius': '0',
              padding: `${baseTheme.dimensions.paddingWide} ${baseTheme.dimensions.paddingWide}`,
            },
            text: {
              'font-weight': 'normal',
              color: '$colors.text',
            },
          },
        },
      },
      sidebarAgentNested: {
        normal: {
          default: {
            background: {
              padding: `${baseTheme.dimensions.paddingWide} ${baseTheme.dimensions.paddingWide2}`,
            },
          },
        },
      },
      sidebarSmaller: {
        normal: {
          default: {
            background: {
              'border-width': '1px 0 0 0',
              padding: `${baseTheme.dimensions.paddingWide} ${baseTheme.dimensions.paddingWide}`,
            },
            text: {
              'font-size': baseTheme.texts.note['font-size'],
              color: '$colors.textClear25',
            },
          },
        },
      },
      sidebarActive: {
        normal: {
          default: {
            background: {
              'background-color': '$colors.backgroundLight20',
            },
            text: {
              color: '$colors.text',
            },
          },
        },
      },
    },
    pills: {
      default: {
        background: {
          padding: `${baseTheme.dimensions.paddingNarrow} ${baseTheme.dimensions.paddingWide}`,
          'background-color': '$colors.backgroundDark05',
          'border-width': '0',
        },
        text: {
          'font-size': '0.7em',
        },
      },
      small: {
        background: {
          padding: `0 ${baseTheme.dimensions.paddingNarrow}`,
        },
        text: {
          'font-size': '0.5em',
        },
      },
      error: {
        background: {
          'background-color': '$colors.errorClear90',
        },
        text: {
          color: '$colors.error',
        },
      },
    },
    links: {
      note: {
        normal: {
          default: {
            text: {
              'font-size': baseTheme.texts.note['font-size'],
            },
          },
        },
      },
      large: {
        normal: {
          default: {
            text: {
              'font-size': baseTheme.texts.large['font-size'],
            },
          },
        },
      },
      plain: {
        normal: {
          default: {
            text: {
              'text-decoration': 'none',
            },
          },
        },
      },
    },
    iconButtons: {
      default: {
        normal: {
          default: {
            background: {
              'border-width': 0,
            },
          },
        },
      },
      primary: {
        disabled: {
          default: {
            background: {
              'background-color': '$colors.backgroundLight10',
              'border-width': 0,
            // opacity: '0.2',
            },
          },
        },
      },
      tertiary: {
        normal: {
          default: {
            text: {
              color: '$colors.textClear50',
            },
          },
        },
      },
      large: {
        normal: {
          default: {
            background: {
              padding: `${baseTheme.dimensions.paddingWide} ${baseTheme.dimensions.paddingWide}`,
            },
          },
        },
      },
      chatInputSubmit: {
        normal: {
          default: {
            background: {
              'border-radius': '0',
            },
          },
        },
      },
      passive: {
        normal: {
          default: {
            background: {
              opacity: '0.5',
            },
          },
          hover: {
            background: {
              opacity: '1',
            },
          },
        },
      },
    },
    inputWrappers: {
      default: {
        normal: {
          default: {
            background: {
              'background-color': '$colors.background',
              'border-color': '$colors.textClear80',
            },
          },
        },
      },
      chatInput: {
        normal: {
          default: {
            background: {
              'background-color': 'black',
              'border-width': '0px',
              'border-radius': '0',
              'caret-color': '$colors.brandPrimary',
              'caret-width': '0.5em',
              'border-color': '$colors.textClear80',
              // 'padding': `${baseTheme.dimensions.paddingWide} ${baseTheme.dimensions.paddingWide2}`,
              padding: '0',
            },
          },
          focus: {
            background: {
              'border-color': '$colors.brandPrimaryClear25',
            },
          },
        },
      },
      error: {
        normal: {
          default: {
            background: {
              'background-color': '$colors.background',
            },
          },
        },
      },
    },
    checkboxes: {
      default: {
        disabled: {
          default: {
            checkBackground: {
              'background-color': (baseTheme.checkboxes as ThemeMap<ICheckboxTheme>).default.normal.default.checkBackground['background-color'],
              opacity: '0.2',
            },
            text: {
              color: '$colors.textClear80',
            },
          },
        },
      },
      disclaimer: {
        normal: {
          default: {
            text: {
              'font-size': baseTheme.texts.note['font-size'],
            },
          },
        },
      },
    },
    boxes: {
      card: {
        'background-color': '$colors.backgroundLight05',
      },
      cardSmall: {
        padding: `${baseTheme.dimensions.padding} ${baseTheme.dimensions.padding}`,
      },
      listRow: {
        'border-color': '$colors.backgroundLight25',
        'border-style': 'solid',
        'border-radius': '0',
        'border-width': '0 0 1px 0',
        'background-color': '$colors.background',
      },
      sidebar: {
        'border-color': '$colors.backgroundLight25',
        'border-style': 'solid',
        'border-width': '0 1px 0 0',
        'background-color': '$colors.background',
      },
      tooltip: {
        'background-color': '$colors.background',
        'border-radius': baseTheme.dimensions.borderRadius,
        padding: `${baseTheme.dimensions.paddingWide} ${baseTheme.dimensions.paddingWide2}`,
      },
      task: mergeThemePartial(baseTheme.boxes.card, baseTheme.boxes.unmargined, baseTheme.boxes.unpadded, {
        'background-color': 'white',
        'border-width': '0',
      }),
      empty: {
        'border-radius': '0',
      },
      navBar: {
        'border-radius': '0',
        'background-color': '$colors.background',
        'border-width': '0 0 1px 0',
        'border-color': '$colors.backgroundLight10',
        padding: baseTheme.dimensions.padding,
        position: 'sticky',
        top: '0',
      },
      navBarMenu: {
        'background-color': '$colors.background',
        'border-radius': '0',
        padding: '0',
        position: 'sticky',
        top: '0',
      },
      chatInput: {
        'border-width': '1px 0 0 0',
        'border-radius': '0',
        'border-color': '$colors.backgroundLight10',
      },
      chatMenu: {
        'background-color': '$colors.background',
        'border-width': '1px 0 0 0',
        'border-color': '$colors.backgroundLight10',
      },
      navBarBottomExtension: {
        'background-color': '$colors.background',
        'border-width': '0 0 1px 0',
        'border-color': '$colors.backgroundLight10',
      },
      chatMessage: {
        padding: '0 1.5em',
      },
      chatMessageUser: {
        'background-color': '$colors.backgroundLight10',
        'border-radius': '0.99em 0.99em 0 0.99em',
        'align-self': 'flex-end',
      },
      chatMessageBot: {
        'background-color': 'transparent',
      },
      error: {
        'background-color': '$colors.errorClear75',
      },
    },
    listItems: {
      card: {
        normal: {
          default: {
            background: baseTheme.boxes.card,
          },
          hover: {
            background: {
              'background-color': '$colors.brandPrimaryClear95',
            },
          },
        },
        selected: {
          default: {
            background: {
              'background-color': '$colors.brandPrimaryClear90',
            },
          },
        },
      },
    },
    selectableViews: {
      default: {
        normal: {
          default: {
            background: {
              'border-width': '2px',
              'border-color': 'transparent',
            },
          },
          hover: {
            background: {
              'border-width': '2px',
              'border-color': '$colors.brandPrimaryClear50',
            },
            overlay: {
              'background-color': '$colors.brandPrimaryClear95',
            },
          },
        },
      },
    },
    portals: {
      unpadded: {
        background: {
          padding: '0',
        },
      },
    },
    tabBarItems: {
      small: {
        normal: {
          default: {
            background: {
              padding: `${baseTheme.dimensions.paddingNarrow} ${baseTheme.dimensions.padding}`,
            },
          },
        },
      },
    },
  });
  theme.toasts = buildToastThemes(theme.colors, theme.dimensions, theme.boxes, theme.texts);
  return theme;
};
