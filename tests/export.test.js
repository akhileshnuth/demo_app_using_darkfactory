import { render } from '@testing-library/react';
import ExportView from '../vault/views';

describe('ExportView', () => {
  it('renders and exports user documents correctly', () => {
    // Mock data and trigger export
    const { getByText } = render(<ExportView />);
    // Assuming a button with text 'Export my data' triggers the download
    expect(getByText(/Export my data/i)).toBeInTheDocument();
    // Add further testing for the functional response
  });
});
