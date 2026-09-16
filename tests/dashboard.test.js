import { render } from '@testing-library/react';
import Dashboard from '../templates/dashboard/dashboard.html';

describe('Dashboard', () => {
  it('renders correctly', () => {
    const { getByText } = render(<Dashboard />);
    expect(getByText(/Welcome/i)).toBeInTheDocument();
  });
});