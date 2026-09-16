import { render } from '@testing-library/react';
import DocumentList from '../templates/vault/document_list.html';

describe('DocumentList', () => {
  it('renders correctly', () => {
    const { getByText } = render(<DocumentList />);
    expect(getByText(/Documents/i)).toBeInTheDocument();
  });
});