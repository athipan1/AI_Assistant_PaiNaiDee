"""
Sample integration code examples for PaiNaiDee Public API
Examples in Python, JavaScript, PHP, and cURL
"""

# ==============================================================================
# PYTHON EXAMPLE
# ==============================================================================

import requests
import json

class PaiNaiDeeAPI:
    """Python client for PaiNaiDee Public API"""
    
    def __init__(self, api_key, base_url="http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def ask_ai(self, question, language="th", context=None, user_id=None):
        """Ask the AI Assistant a question"""
        url = f"{self.base_url}/api/ai/ask"
        params = {"lang": language}
        data = {
            "question": question,
            "context": context,
            "user_id": user_id
        }
        
        response = requests.post(url, headers=self.headers, params=params, json=data)
        response.raise_for_status()
        return response.json()
    
    def get_trip_recommendations(self, budget="medium", location=None, duration=None, 
                               trip_type=None, interests=None, group_size=1):
        """Get trip recommendations"""
        url = f"{self.base_url}/api/recommend/trip"
        params = {
            "budget": budget,
            "location": location,
            "duration": duration,
            "trip_type": trip_type,
            "interests": ",".join(interests) if interests else None,
            "group_size": group_size
        }
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_image_tour_preview(self, location):
        """Get image tour preview for a location"""
        url = f"{self.base_url}/api/image-tour-preview"
        params = {"location": location}
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

# Usage Example
if __name__ == "__main__":
    # Initialize client
    api = PaiNaiDeeAPI("painaidee_your_api_key_here")
    
    try:
        # Ask AI Assistant
        ai_response = api.ask_ai(
            question="แนะนำร้านอาหารไทยในกรุงเทพฯ", 
            language="th"
        )
        print("AI Response:", ai_response["answer"])
        
        # Get trip recommendations
        trip_recommendations = api.get_trip_recommendations(
            budget="medium",
            location="Bangkok", 
            duration=3,
            interests=["culture", "food"]
        )
        print("Trip Recommendations:", len(trip_recommendations["destinations"]), "places")
        
        # Get image tour preview
        image_tour = api.get_image_tour_preview("เชียงใหม่")
        print("Image Tour:", len(image_tour["images"]), "images available")
        
    except requests.RequestException as e:
        print("API Error:", e)

# ==============================================================================
# JAVASCRIPT EXAMPLE (Node.js)
# ==============================================================================

"""
// package.json
{
  "name": "painaidee-api-client",
  "version": "1.0.0",
  "dependencies": {
    "axios": "^1.0.0"
  }
}

// painaidee-client.js
const axios = require('axios');

class PaiNaiDeeAPI {
    constructor(apiKey, baseUrl = 'http://localhost:8000') {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
        this.client = axios.create({
            baseURL: baseUrl,
            headers: {
                'Authorization': `Bearer ${apiKey}`,
                'Content-Type': 'application/json'
            }
        });
    }

    async askAI(question, language = 'th', context = null, userId = null) {
        try {
            const response = await this.client.post('/api/ai/ask', {
                question,
                context,
                user_id: userId
            }, {
                params: { lang: language }
            });
            
            return response.data;
        } catch (error) {
            throw new Error(`AI Ask failed: ${error.response?.data?.detail || error.message}`);
        }
    }

    async getTripRecommendations({
        budget = 'medium',
        location = null,
        duration = null,
        tripType = null,
        interests = null,
        groupSize = 1
    } = {}) {
        try {
            const params = {
                budget,
                group_size: groupSize
            };
            
            if (location) params.location = location;
            if (duration) params.duration = duration;
            if (tripType) params.trip_type = tripType;
            if (interests) params.interests = interests.join(',');
            
            const response = await this.client.get('/api/recommend/trip', { params });
            return response.data;
        } catch (error) {
            throw new Error(`Trip recommendations failed: ${error.response?.data?.detail || error.message}`);
        }
    }

    async getImageTourPreview(location) {
        try {
            const response = await this.client.get('/api/image-tour-preview', {
                params: { location }
            });
            return response.data;
        } catch (error) {
            throw new Error(`Image tour preview failed: ${error.response?.data?.detail || error.message}`);
        }
    }
}

// Usage Example
async function example() {
    const api = new PaiNaiDeeAPI('painaidee_your_api_key_here');

    try {
        // Ask AI Assistant
        const aiResponse = await api.askAI(
            'แนะนำสถานที่ท่องเที่ยวในกรุงเทพฯ',
            'th'
        );
        console.log('AI Response:', aiResponse.answer);

        // Get trip recommendations
        const tripRecs = await api.getTripRecommendations({
            budget: 'low',
            location: 'Bangkok',
            duration: 2,
            interests: ['temples', 'food']
        });
        console.log('Trip Recommendations:', tripRecs.destinations.length, 'places');

        // Get image tour preview
        const imageTour = await api.getImageTourPreview('Phuket');
        console.log('Image Tour:', imageTour.images.length, 'images');

    } catch (error) {
        console.error('API Error:', error.message);
    }
}

example();

module.exports = PaiNaiDeeAPI;
"""

# ==============================================================================
# PHP EXAMPLE
# ==============================================================================

"""
<?php
// PaiNaiDeeAPI.php

class PaiNaiDeeAPI {
    private $apiKey;
    private $baseUrl;
    
    public function __construct($apiKey, $baseUrl = 'http://localhost:8000') {
        $this->apiKey = $apiKey;
        $this->baseUrl = $baseUrl;
    }
    
    private function makeRequest($method, $endpoint, $data = null, $params = []) {
        $url = $this->baseUrl . $endpoint;
        
        if (!empty($params)) {
            $url .= '?' . http_build_query($params);
        }
        
        $headers = [
            'Authorization: Bearer ' . $this->apiKey,
            'Content-Type: application/json'
        ];
        
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        
        if ($method === 'POST') {
            curl_setopt($ch, CURLOPT_POST, true);
            if ($data) {
                curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
            }
        }
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($httpCode >= 400) {
            $error = json_decode($response, true);
            throw new Exception($error['detail'] ?? 'API request failed');
        }
        
        return json_decode($response, true);
    }
    
    public function askAI($question, $language = 'th', $context = null, $userId = null) {
        $data = [
            'question' => $question,
            'context' => $context,
            'user_id' => $userId
        ];
        
        $params = ['lang' => $language];
        
        return $this->makeRequest('POST', '/api/ai/ask', $data, $params);
    }
    
    public function getTripRecommendations($options = []) {
        $defaults = [
            'budget' => 'medium',
            'location' => null,
            'duration' => null,
            'trip_type' => null,
            'interests' => null,
            'group_size' => 1
        ];
        
        $params = array_merge($defaults, $options);
        
        if (is_array($params['interests'])) {
            $params['interests'] = implode(',', $params['interests']);
        }
        
        // Remove null values
        $params = array_filter($params, function($value) {
            return $value !== null;
        });
        
        return $this->makeRequest('GET', '/api/recommend/trip', null, $params);
    }
    
    public function getImageTourPreview($location) {
        $params = ['location' => $location];
        return $this->makeRequest('GET', '/api/image-tour-preview', null, $params);
    }
}

// Usage Example
try {
    $api = new PaiNaiDeeAPI('painaidee_your_api_key_here');
    
    // Ask AI Assistant
    $aiResponse = $api->askAI(
        'ช่วยแนะนำโรงแรมดีๆ ในภูเก็ต',
        'th'
    );
    echo "AI Response: " . $aiResponse['answer'] . "\n";
    
    // Get trip recommendations
    $tripRecs = $api->getTripRecommendations([
        'budget' => 'high',
        'location' => 'Phuket',
        'duration' => 5,
        'interests' => ['beach', 'nightlife']
    ]);
    echo "Trip Recommendations: " . count($tripRecs['destinations']) . " places\n";
    
    // Get image tour preview
    $imageTour = $api->getImageTourPreview('กรุงเทพฯ');
    echo "Image Tour: " . count($imageTour['images']) . " images\n";
    
} catch (Exception $e) {
    echo "API Error: " . $e->getMessage() . "\n";
}
?>
"""

# ==============================================================================
# cURL EXAMPLES
# ==============================================================================

"""
#!/bin/bash
# painaidee-api-examples.sh

# Set your API key
API_KEY="painaidee_your_api_key_here"
BASE_URL="http://localhost:8000"

# Example 1: Ask AI Assistant
echo "=== AI Assistant Example ==="
curl -X POST "${BASE_URL}/api/ai/ask?lang=th" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "แนะนำอาหารไทยที่ต้องลอง",
    "context": {"user_location": "Bangkok"},
    "user_id": "user123"
  }' | jq '.'

echo -e "\n=== Trip Recommendations Example ==="
curl -X GET "${BASE_URL}/api/recommend/trip?budget=medium&location=Bangkok&duration=3&interests=culture,food&group_size=2" \
  -H "Authorization: Bearer ${API_KEY}" | jq '.'

echo -e "\n=== Image Tour Preview Example ==="
curl -X GET "${BASE_URL}/api/image-tour-preview?location=เชียงใหม่" \
  -H "Authorization: Bearer ${API_KEY}" | jq '.'

echo -e "\n=== Health Check Example ==="
curl -X GET "${BASE_URL}/api/health" | jq '.'
"""

# ==============================================================================
# REACT/JAVASCRIPT FRONTEND EXAMPLE
# ==============================================================================

"""
// hooks/usePaiNaiDeeAPI.js
import { useState, useCallback } from 'react';

const usePaiNaiDeeAPI = (apiKey) => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    
    const baseUrl = 'http://localhost:8000';
    
    const makeRequest = useCallback(async (endpoint, options = {}) => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await fetch(`${baseUrl}${endpoint}`, {
                headers: {
                    'Authorization': `Bearer ${apiKey}`,
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'API request failed');
            }
            
            return await response.json();
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [apiKey, baseUrl]);
    
    const askAI = useCallback(async (question, language = 'th', context = null) => {
        const params = new URLSearchParams({ lang: language });
        return makeRequest(`/api/ai/ask?${params}`, {
            method: 'POST',
            body: JSON.stringify({
                question,
                context,
                user_id: 'web-user'
            })
        });
    }, [makeRequest]);
    
    const getTripRecommendations = useCallback(async (options = {}) => {
        const params = new URLSearchParams();
        
        if (options.budget) params.append('budget', options.budget);
        if (options.location) params.append('location', options.location);
        if (options.duration) params.append('duration', options.duration);
        if (options.tripType) params.append('trip_type', options.tripType);
        if (options.interests) params.append('interests', options.interests.join(','));
        if (options.groupSize) params.append('group_size', options.groupSize);
        
        return makeRequest(`/api/recommend/trip?${params}`);
    }, [makeRequest]);
    
    const getImageTourPreview = useCallback(async (location) => {
        const params = new URLSearchParams({ location });
        return makeRequest(`/api/image-tour-preview?${params}`);
    }, [makeRequest]);
    
    return {
        loading,
        error,
        askAI,
        getTripRecommendations,
        getImageTourPreview
    };
};

export default usePaiNaiDeeAPI;

// components/TourismWidget.jsx
import React, { useState } from 'react';
import usePaiNaiDeeAPI from '../hooks/usePaiNaiDeeAPI';

const TourismWidget = ({ apiKey }) => {
    const [question, setQuestion] = useState('');
    const [response, setResponse] = useState(null);
    const { loading, error, askAI, getTripRecommendations } = usePaiNaiDeeAPI(apiKey);
    
    const handleAskAI = async () => {
        try {
            const result = await askAI(question, 'th');
            setResponse(result);
        } catch (err) {
            console.error('AI request failed:', err);
        }
    };
    
    const handleGetRecommendations = async () => {
        try {
            const result = await getTripRecommendations({
                budget: 'medium',
                location: 'Bangkok',
                interests: ['culture', 'food']
            });
            setResponse(result);
        } catch (err) {
            console.error('Recommendations request failed:', err);
        }
    };
    
    return (
        <div className="tourism-widget">
            <h2>PaiNaiDee Tourism Assistant</h2>
            
            <div className="input-section">
                <input
                    type="text"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="ถามเกี่ยวกับการท่องเที่ยวไทย..."
                    className="question-input"
                />
                <button onClick={handleAskAI} disabled={loading}>
                    {loading ? 'กำลังประมวลผล...' : 'ถาม AI'}
                </button>
            </div>
            
            <div className="actions">
                <button onClick={handleGetRecommendations} disabled={loading}>
                    แนะนำสถานที่ท่องเที่ยว
                </button>
            </div>
            
            {error && (
                <div className="error">Error: {error}</div>
            )}
            
            {response && (
                <div className="response">
                    <h3>Response:</h3>
                    <pre>{JSON.stringify(response, null, 2)}</pre>
                </div>
            )}
        </div>
    );
};

export default TourismWidget;
"""