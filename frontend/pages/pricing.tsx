import styled from 'styled-components';
import Page from 'frontend/components/Page';
import FaqSection from 'frontend/views/PricingPage/FaqSection';
import PricingTablesSection from 'frontend/views/PricingPage/PricingTablesSection';

export default function PricingPage() {
  return (
    <Page title="Pricing" description="Cupidatat et reprehenderit ullamco aute ullamco anim tempor.">
      <Wrapper>
        <PricingTablesSection />
        <FaqSection />
      </Wrapper>
    </Page>
  );
}

const Wrapper = styled.div`
  & > :last-child {
    margin-bottom: 15rem;
  }
`;
