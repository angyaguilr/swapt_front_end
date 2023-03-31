import styled from 'styled-components';
import Page from 'frontend/components/Page';
import { media } from 'frontend/utils/media';
import FormSection from 'frontend/views/ContactPage/FormSection';
import InformationSection from 'frontend/views/ContactPage/InformationSection';

export default function ContactPage() {
  return (
    <Page title="Contact" description="Minim sint aliquip nostrud excepteur cupidatat amet do laborum exercitation cupidatat ea proident.">
      <ContactContainer>
        <InformationSection />
        <FormSection />
      </ContactContainer>
    </Page>
  );
}

const ContactContainer = styled.div`
  display: flex;

  ${media('<=tablet')} {
    flex-direction: column;
  }
`;
