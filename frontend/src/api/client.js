const BASE_URL = 'http://localhost:8000/api/v1';

export const apiClient = {
  getHealth: async () => {
    const response = await fetch(`${BASE_URL}/health`);
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    return response.json();
  },
};
