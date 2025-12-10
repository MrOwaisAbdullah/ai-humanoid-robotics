import React from 'react';
import DocItem from '@theme-original/DocItem';
import type {Props} from '@theme/DocItem';

export default function DocItemWrapper(props: Props): JSX.Element {
  return <DocItem {...props} />;
}
