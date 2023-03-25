import React from 'react';
import styled from 'styled-components';
import AutofitGrid from 'components/AutofitGrid';
import BasicCard from 'components/BasicCard';
import Container from 'components/Container';
import OverTitle from 'components/OverTitle';
import SectionTitle from 'components/SectionTitle';
import { media } from 'utils/media';

const FEATURES = [
  {
    imageUrl: '/grid-icons/asset-1.svg',
    title: '1.',
    description:
      'Search for your next apartment',
  },
  {
    imageUrl: '/grid-icons/asset-4.svg',
    title: '2.',
    description:
      'Make an offer',
  },
  {
    imageUrl: '/grid-icons/asset-3.svg',
    title: '3.',
    description:
      'Check the community marketplace for anything else you need',
  },
];

export default function Features() {
  return (
    <Container>
       <Content>
        <OverTitle></OverTitle>
        <SectionTitle>How it Works</SectionTitle>
      </Content>
      <CustomAutofitGrid>
        {FEATURES.map((singleFeature, idx) => (
          <BasicCard key={singleFeature.title} {...singleFeature} />
        ))}
      </CustomAutofitGrid>
    </Container>
  );
}
const Content = styled.div`
  & > *:not(:first-child) {
    margin-top: 1rem;
  }
  text-align: center;
`;

const CustomAutofitGrid = styled(AutofitGrid)`
  --autofit-grid-item-size: 40rem;

  ${media('<=tablet')} {
    --autofit-grid-item-size: 30rem;
  }

  ${media('<=phone')} {
    --autofit-grid-item-size: 100%;
  }
`;

