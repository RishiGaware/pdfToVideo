import { useState, useEffect } from 'react';
import { apiClient } from '../../api/client';
import '../../styles/App.css';

function Home() {
  const [health, setHealth] = useState('Checking...');

  useEffect(() => {
    apiClient.getHealth()
      .then(data => setHealth(data.status))
      .catch(err => {
        console.error(err);
        setHealth('Offline');
      });
  }, []);

  return (
    <div className="Home">
      <h1>pdfToVideo Dashboard</h1>
      <div className="card">
        <p>
          Backend Status: <strong>{health}</strong>
        </p>
      </div>
      <p className="read-the-docs">
        Ready for some PDF to Video magic!
      </p>
    </div>
  );
}

export default Home;
