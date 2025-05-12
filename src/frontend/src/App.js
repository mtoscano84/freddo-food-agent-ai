import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import './App.css';

// Fix for default marker icons in Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
    iconUrl: require('leaflet/dist/images/marker-icon.png'),
    shadowUrl: require('leaflet/dist/images/marker-shadow.png')
});

function StoreMap({ stores, userLocation }) {
  const mapStyles = {
    height: "300px",
    width: "100%",
    borderRadius: "8px",
    margin: "10px 0"
  };

  // Default to Barcelona's coordinates
  const defaultCenter = [41.3851, 2.1734];
  
  // Validate coordinates before using them
  const center = userLocation && !isNaN(userLocation.lat) && !isNaN(userLocation.lng)
    ? [userLocation.lat, userLocation.lng]
    : defaultCenter;

  // Custom icons
  const userIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
  });

  return (
    <MapContainer 
      center={center}
      zoom={13} 
      style={mapStyles}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />
      {userLocation && (
        <Marker 
          position={[userLocation.lat, userLocation.lng]}
          icon={userIcon}
        >
          <Popup>
            <strong>Your Location</strong><br />
            {userLocation.address}
          </Popup>
        </Marker>
      )}
      {stores.map((store, index) => (
        <Marker 
          key={index}
          position={[store.lat, store.lng]}
        >
          <Popup>
            <strong>{store.name}</strong><br />
            Distance: {(store.distance_meters / 1000).toFixed(2)} km
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}

// Instead of relying on build-time env variables, use window._env_ for runtime config
const BACKEND_URL = window.location.hostname === 'localhost' 
  ? 'http://localhost:5001'
  : 'https://freddo-backend-316231368980.us-central1.run.app';

console.log('Using backend URL:', BACKEND_URL); // For debugging

function formatMessage(text) {
  // Handle recipe list format
  if (text.includes('Here are some recipes:')) {
    const lines = text.split('\n');
    const isRecipeList = lines.some(line => line.match(/^\•/) && !line.includes(':'));
    
    return (
      <div className="recipes-container">
        <h2 className="recipes-title">
          <span>📖</span> Available Recipes
        </h2>
        <ul className="recipes-list">
          {lines.map((line, index) => {
            if (isRecipeList && line.match(/^\•/)) {
              const recipeName = line.replace(/^\•/, '').trim();
              const imageUrl = `${BACKEND_URL}/images/${recipeName}.png`;
              
              return (
                <li key={index} className="recipe-item">
                  <div className="recipe-content">
                    <img 
                      src={imageUrl}
                      alt={recipeName}
                      onError={(e) => {
                        console.log(`Failed to load image: ${imageUrl}`);
                        e.target.style.display = 'none';
                      }}
                      className="recipe-image"
                    />
                    <div className="recipe-text">{recipeName}</div>
                  </div>
                </li>
              );
            }
            return null;
          }).filter(Boolean)}
        </ul>
      </div>
    );
  }

  // Check if this is a shopping list
  if (text.includes('Shopping List:')) {
    const items = text
      .split('\n')
      .filter(line => line.trim()) // Remove empty lines
      .slice(2); // Skip the header and empty line

    const getItemIcon = (item) => {
      const itemLower = item.toLowerCase();
      if (itemLower.includes('chicken')) return '🍗';
      if (itemLower.includes('egg')) return '🥚';
      if (itemLower.includes('lettuce') || itemLower.includes('salad') || itemLower.includes('greens')) return '🥬';
      if (itemLower.includes('pepper')) return '🫑';
      if (itemLower.includes('onion')) return '🧅';
      if (itemLower.includes('corn')) return '🌽';
      if (itemLower.includes('bean')) return '🫘';
      if (itemLower.includes('avocado')) return '🥑';
      if (itemLower.includes('cream')) return '🥛';
      if (itemLower.includes('coffee')) return '☕';
      if (itemLower.includes('berry') || itemLower.includes('berries')) return '🫐';
      if (itemLower.includes('sugar')) return '🧂';
      if (itemLower.includes('cocoa') || itemLower.includes('chocolate')) return '🍫';
      return '•';
    };

    return (
      <div className="shopping-list-container">
        <h2 className="shopping-list-title">
          <span>🛒</span> Shopping List
        </h2>
        <div className="shopping-list-items">
          {items.map((item, index) => (
            <div key={index} className="shopping-list-item">
              <span className="item-text">
                <span className="item-icon">{getItemIcon(item)}</span>
                {item}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Check if this is a store list (contains coordinates)
  if (text.includes('Express|') || text.includes('Market|')) {
    try {
      // Split the text into store entries
      const entries = text.split(/(?=Cont Express\|)|(?=Al Supermarket\|)|(?=Li Market\|)/);
      console.log('Entries:', entries);

      const stores = entries.map(entry => {
        const parts = entry.trim().split(/[\|,]/);
        console.log('Store parts:', parts);
        
        return {
          type: 'store',
          name: parts[0].trim(),
          distance_meters: parseFloat(parts[1]),
          lat: parseFloat(parts[2]),
          lng: parseFloat(parts[3])
        };
      }).filter(store => !isNaN(store.lat) && !isNaN(store.lng));

      // Use Barcelona coordinates for user location
      const userLocation = {
        type: 'user',
        address: 'Your Location',
        lat: 41.385273,
        lng: 2.161236
      };

      console.log('User location:', userLocation);
      console.log('Stores:', stores);

      return (
        <div className="stores-container">
          <div className="stores-list">
            <div className="user-location">
              <h3>📍 Your Location</h3>
              <p>{userLocation.address}</p>
            </div>
            {stores.map((store, index) => (
              <div key={index} className="store-item">
                <h3>🏪 {store.name}</h3>
                <p>Distance: {(store.distance_meters / 1000).toFixed(2)} km</p>
              </div>
            ))}
          </div>
          <StoreMap stores={stores} userLocation={userLocation} />
        </div>
      );
    } catch (e) {
      console.error('Error parsing store locations:', e);
      return <p>{text}</p>;
    }
  }

  // Handle order display format
  if (text.includes('order_id:')) {
    const orderMatch = text.match(/order_id: (\d+), total: ([\d.]+), status: (\w+), delivery method: (\w+)/);
    if (orderMatch) {
      const [_, id, total, status, method] = orderMatch;
      
      return (
        <div className="order-confirmation-container">
          <div className="order-header">
            <span className="order-icon">📦</span>
            <h2>Order Status</h2>
          </div>
          <div className="order-details">
            <div className="detail-row">
              <span className="detail-label">Order #</span>
              <span className="detail-value">{id}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Total</span>
              <span className="detail-value">${parseFloat(total).toFixed(2)}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Status</span>
              <span className={`order-status ${status.toLowerCase()}`}>
                {status}
              </span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Delivery Method</span>
              <span className="detail-value">{method}</span>
            </div>
          </div>
        </div>
      );
    }
  }

  // Handle delivery policy format
  if (text.includes('Delivery|') || (text.includes('Supermarket') && text.includes('|'))) {
    const policies = text.split('\n').filter(line => line.trim()).map(line => {
      // Split on | but keep the store name together if it contains spaces
      const parts = line.split('|');
      return {
        store_name: parts[0].trim(),
        delivery_method: parts[1].trim(),
        delivery_time: parts[2].trim(),
        fee: parts[3].trim() // Remove parseFloat to keep original format
      };
    });

    return (
      <div className="policy-container">
        <div className="policy-header">
          <span className="policy-icon">🚚</span>
          <h2>Delivery Methods</h2>
        </div>
        <table className="policy-table">
          <thead>
            <tr>
              <th>Store</th>
              <th>Delivery Method</th>
              <th>Delivery Time</th>
              <th>Fee</th>
            </tr>
          </thead>
          <tbody>
            {policies.map((policy, index) => (
              <tr key={index}>
                <td>{policy.store_name}</td>
                <td>{policy.delivery_method}</td>
                <td>{policy.delivery_time}</td>
                <td>{policy.fee}</td> {/* Remove .toFixed(2) to show original value */}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  // Default text display
  return text;
}

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Show welcome message when component mounts
  useEffect(() => {
    setMessages([{
      text: "👋 Hi! I'm Freddo, your cooking assistant. Ask me about recipes!",
      sender: 'freddo'
    }]);
  }, []);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    const userMessage = { text: inputMessage, sender: 'user' };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
        const url = `${BACKEND_URL}/chat`;
        console.log('Sending request to:', url);  // Debug log
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: inputMessage }),
        });

        console.log('Response status:', response.status);  // Debug log
        const data = await response.json();
        console.log('Response data:', data);  // Debug log
        
        if (!response.ok) {
            throw new Error(`Server error: ${data.error || 'Unknown error'}`);
        }
        
        const freddoMessage = { 
            text: data.response || 'No response from server', 
            sender: 'freddo' 
        };
        
        setMessages(prev => [...prev, freddoMessage]);
    } catch (error) {
        console.error('Chat error:', error);
        setMessages(prev => [...prev, {
            text: `Error: ${error.message}`,
            sender: 'freddo'
        }]);
    } finally {
        setIsLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🧑‍🍳 Freddo - Your Cooking Assistant</h1>
      </header>
      <div className="chat-container">
        <div className="chat-messages">
          {messages.map((message, index) => (
            <div key={index} className={`message ${message.sender}`}>
              {message.sender === 'freddo' && <span className="avatar">🧑‍🍳</span>}
              <div className="message-content">
                {message.sender === 'freddo' ? (
                  <div className="formatted-content">
                    {formatMessage(message.text)}
                  </div>
                ) : (
                  message.text
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="message freddo">
              <span className="avatar">🧑‍🍳</span>
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
        </div>
        <form onSubmit={handleSendMessage} className="chat-input">
          <input 
            type="text" 
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Ask Freddo about recipes..."
            disabled={isLoading}
          />
          <button type="submit" disabled={isLoading}>
            {isLoading ? '...' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;