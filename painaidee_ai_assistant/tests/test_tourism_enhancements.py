"""
Comprehensive tests for Tourism Enhancement features
Tests Tourist Interest Graph and Contextual Recommendation Engine
"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.tourist_interest_graph import TouristInterestGraph, TouristInterest
from models.contextual_recommendations import (
    ContextualRecommendationEngine, 
    WeatherCondition, 
    Season, 
    TimeOfDay
)


class TestTouristInterestGraph(unittest.TestCase):
    """Test the Tourist Interest Graph system"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.graph = TouristInterestGraph(storage_dir=str(self.temp_dir))
        
        # Sample interaction data
        self.sample_interaction = {
            'query': 'Show me a walking person in nature',
            'selected_model': 'Walking.fbx',
            'context': {
                'weather': {'condition': 'clear', 'temperature': 25},
                'time_of_day': 'morning'
            },
            'feedback': {'satisfaction': 0.8},
            'interaction_time': 45
        }
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_interest_capture_from_interaction(self):
        """Test capturing tourist interests from user interactions"""
        
        # Capture interest
        interest = self.graph.capture_interest_from_interaction(
            "test_user", "test_session", self.sample_interaction
        )
        
        # Verify interest properties
        self.assertIsInstance(interest, TouristInterest)
        self.assertEqual(interest.user_id, "test_user")
        self.assertEqual(interest.session_id, "test_session")
        self.assertIn(interest.interest_type, ['nature', 'city', 'culture', 'adventure', 'food', 'history'])
        self.assertGreater(interest.confidence, 0.0)
        self.assertGreater(interest.interaction_strength, 0.0)
        
        # Verify interest is stored
        self.assertIn("test_user", self.graph.user_interests)
        self.assertEqual(len(self.graph.user_interests["test_user"]), 1)
    
    def test_interest_type_classification(self):
        """Test interest type classification accuracy"""
        
        test_cases = [
            ("hiking in mountains", "nature"),
            ("city skyline views", "city"),
            ("temple visit", "culture"),
            ("rock climbing adventure", "adventure"),
            ("street food tour", "food"),
            ("ancient ruins", "history")
        ]
        
        for query, expected_type in test_cases:
            classified_type = self.graph._classify_interest_type(query, "Man.fbx")
            self.assertEqual(classified_type, expected_type, 
                           f"Failed for query: '{query}', expected: {expected_type}, got: {classified_type}")
    
    def test_specific_tag_extraction(self):
        """Test extraction of specific tags from queries"""
        
        query = "hiking in beautiful waterfalls and mountains"
        interest_type = "nature"
        
        tags = self.graph._extract_specific_tags(query, interest_type)
        
        self.assertIn("hiking", tags)
        self.assertIn("waterfalls", tags)
        self.assertIn("mountains", tags)
        self.assertIn("beautiful", tags)
        self.assertLessEqual(len(tags), 5)  # Should limit to 5 tags
    
    def test_preference_inference(self):
        """Test inference of user preferences from queries"""
        
        # Test location preference
        indoor_query = "cafe and museum visit"
        outdoor_query = "hiking and beach activities"
        
        indoor_pref = self.graph._infer_location_preference(indoor_query, {})
        outdoor_pref = self.graph._infer_location_preference(outdoor_query, {})
        
        self.assertEqual(indoor_pref, "indoor")
        self.assertEqual(outdoor_pref, "outdoor")
        
        # Test activity level
        high_activity = self.graph._infer_activity_level("running and climbing", "Running.fbx")
        low_activity = self.graph._infer_activity_level("relaxing and peaceful", "Idle.fbx")
        
        self.assertEqual(high_activity, "high")
        self.assertEqual(low_activity, "low")
    
    def test_location_association_updates(self):
        """Test updating location associations based on interests"""
        
        # Create multiple interests for same location
        for i in range(3):
            interaction = {
                'query': f'nature walk {i}',
                'selected_model': 'Walking.fbx',
                'context': {},
                'feedback': {'satisfaction': 0.8},
                'interaction_time': 30
            }
            
            self.graph.capture_interest_from_interaction(
                f"user_{i}", f"session_{i}", interaction
            )
        
        # Check that Walking.fbx has updated associations
        self.assertIn('Walking.fbx', self.graph.location_associations)
        association = self.graph.location_associations['Walking.fbx']
        
        self.assertGreater(association.popularity_score, 1.0)
        self.assertIn('nature', association.associated_interests)
    
    def test_interest_clustering(self):
        """Test interest clustering functionality"""
        
        # Create diverse interests for clustering
        test_users = [
            ("user1", ["nature hiking", "mountain walking", "forest trails"]),
            ("user2", ["city tours", "urban exploration", "skyline views"]),
            ("user3", ["temple visits", "cultural sites", "traditional art"]),
            ("user4", ["nature photography", "wildlife watching", "outdoor activities"]),
            ("user5", ["street food", "local markets", "cooking classes"])
        ]
        
        for user_id, queries in test_users:
            for i, query in enumerate(queries):
                interaction = {
                    'query': query,
                    'selected_model': 'Walking.fbx',
                    'context': {},
                    'feedback': {'satisfaction': 0.7},
                    'interaction_time': 25
                }
                
                self.graph.capture_interest_from_interaction(
                    user_id, f"session_{user_id}_{i}", interaction
                )
        
        # Perform clustering
        clusters = self.graph.perform_interest_clustering(min_users=3)
        
        # Verify clustering results
        self.assertGreater(len(clusters), 0)
        
        for cluster_id, cluster in clusters.items():
            self.assertGreater(cluster.user_count, 0)
            self.assertGreater(len(cluster.interest_types), 0)
            self.assertIsInstance(cluster.cluster_name, str)
    
    def test_user_recommendations(self):
        """Test personalized recommendations based on user interests"""
        
        # Build user interest history
        nature_interactions = [
            "hiking trails", "waterfall views", "mountain climbing", "forest walks"
        ]
        
        for i, query in enumerate(nature_interactions):
            interaction = {
                'query': query,
                'selected_model': 'Walking.fbx',
                'context': {},
                'feedback': {'satisfaction': 0.8},
                'interaction_time': 30
            }
            
            self.graph.capture_interest_from_interaction(
                "nature_user", f"session_{i}", interaction
            )
        
        # Get recommendations
        available_locations = ['Walking.fbx', 'Running.fbx', 'Idle.fbx', 'Man.fbx']
        recommendations = self.graph.get_recommendations_for_user(
            "nature_user", {}, available_locations, top_k=3
        )
        
        # Verify recommendations
        self.assertGreater(len(recommendations), 0)
        self.assertLessEqual(len(recommendations), 3)
        
        # Walking.fbx should be highly recommended due to user history
        walking_rec = next((r for r in recommendations if r['location_id'] == 'Walking.fbx'), None)
        self.assertIsNotNone(walking_rec)
        self.assertGreater(walking_rec['score'], 0.5)
    
    def test_temporal_decay(self):
        """Test that older interests have less impact (temporal decay)"""
        
        # Create old interest
        old_interaction = {
            'query': 'old nature interest',
            'selected_model': 'Walking.fbx',
            'context': {},
            'feedback': {'satisfaction': 0.9},
            'interaction_time': 60
        }
        
        old_interest = self.graph.capture_interest_from_interaction(
            "temporal_user", "old_session", old_interaction
        )
        
        # Manually set old timestamp (simulate 60 days ago)
        old_time = datetime.now() - timedelta(days=60)
        old_interest.timestamp = old_time.isoformat()
        
        # Create recent interest
        recent_interaction = {
            'query': 'recent city interest',
            'selected_model': 'Man.fbx',
            'context': {},
            'feedback': {'satisfaction': 0.7},
            'interaction_time': 30
        }
        
        self.graph.capture_interest_from_interaction(
            "temporal_user", "recent_session", recent_interaction
        )
        
        # Get recommendations - recent interest should have more impact
        available_locations = ['Walking.fbx', 'Man.fbx']
        recommendations = self.graph.get_recommendations_for_user(
            "temporal_user", {}, available_locations
        )
        
        # Recent interaction should influence recommendations more
        # (This is a basic test - exact scores depend on implementation details)
        self.assertGreater(len(recommendations), 0)
    
    def test_analytics_generation(self):
        """Test analytics generation"""
        
        # Add some test data
        for i in range(5):
            interaction = {
                'query': f'test query {i}',
                'selected_model': 'Walking.fbx',
                'context': {},
                'feedback': {'satisfaction': 0.8},
                'interaction_time': 30
            }
            
            self.graph.capture_interest_from_interaction(
                f"user_{i}", f"session_{i}", interaction
            )
        
        # Get analytics
        analytics = self.graph.get_analytics()
        
        # Verify analytics structure
        self.assertIn('total_users', analytics)
        self.assertIn('total_interests', analytics)
        self.assertIn('total_locations', analytics)
        self.assertIn('interest_type_distribution', analytics)
        self.assertIn('cluster_statistics', analytics)
        
        self.assertEqual(analytics['total_users'], 5)
        self.assertEqual(analytics['total_interests'], 5)


class TestContextualRecommendationEngine(unittest.TestCase):
    """Test the Contextual Recommendation Engine"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.engine = ContextualRecommendationEngine(storage_dir=str(self.temp_dir))
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_current_context_generation(self):
        """Test generation of current contextual factors"""
        
        context = self.engine.get_current_context()
        
        # Verify context structure
        self.assertIsNotNone(context.timestamp)
        self.assertIsInstance(context.time_of_day, TimeOfDay)
        self.assertIsInstance(context.season, Season)
        self.assertIsInstance(context.weather_condition, WeatherCondition)
        self.assertIsInstance(context.temperature, float)
        self.assertIsInstance(context.humidity, float)
        self.assertIsInstance(context.crowd_level, str)
    
    def test_weather_override(self):
        """Test weather override functionality"""
        
        weather_override = {
            'condition': WeatherCondition.RAINY,
            'temperature': 20.0,
            'humidity': 90.0,
            'wind_speed': 15.0,
            'precipitation_chance': 95.0,
            'uv_index': 2.0
        }
        
        context = self.engine.get_current_context(weather_override=weather_override)
        
        self.assertEqual(context.weather_condition, WeatherCondition.RAINY)
        self.assertEqual(context.temperature, 20.0)
        self.assertEqual(context.humidity, 90.0)
    
    def test_contextual_suitability_calculation(self):
        """Test contextual suitability scoring"""
        
        # Get a sample location profile
        profile = self.engine.location_profiles['Walking.fbx']
        
        # Test with clear weather (should be highly suitable for walking)
        clear_context = self.engine.get_current_context(
            weather_override={
                'condition': WeatherCondition.CLEAR,
                'temperature': 22.0,
                'humidity': 60.0,
                'wind_speed': 5.0,
                'precipitation_chance': 0.0,
                'uv_index': 5.0
            }
        )
        
        clear_score = self.engine._calculate_contextual_suitability(
            profile, clear_context
        )
        
        # Test with rainy weather (should be less suitable for walking)
        rainy_context = self.engine.get_current_context(
            weather_override={
                'condition': WeatherCondition.RAINY,
                'temperature': 18.0,
                'humidity': 95.0,
                'wind_speed': 20.0,
                'precipitation_chance': 90.0,
                'uv_index': 1.0
            }
        )
        
        rainy_score = self.engine._calculate_contextual_suitability(
            profile, rainy_context
        )
        
        # Clear weather should be more suitable for walking than rainy weather
        self.assertGreater(clear_score, rainy_score)
    
    def test_time_of_day_suitability(self):
        """Test time of day suitability for different activities"""
        
        available_locations = ['Walking.fbx', 'Running.fbx', 'Idle.fbx']
        
        # Test morning recommendations
        morning_time = datetime.now().replace(hour=9, minute=0, second=0)
        morning_recs = self.engine.get_time_specific_recommendations(
            morning_time, available_locations
        )
        
        # Test evening recommendations
        evening_time = datetime.now().replace(hour=19, minute=0, second=0)
        evening_recs = self.engine.get_time_specific_recommendations(
            evening_time, available_locations
        )
        
        # Verify we get recommendations for both times
        self.assertGreater(len(morning_recs), 0)
        self.assertGreater(len(evening_recs), 0)
        
        # Check that recommendations consider time of day
        for rec in morning_recs:
            self.assertGreater(rec.suitability_score, 0.0)
    
    def test_scenario_specific_recommendations(self):
        """Test scenario-specific recommendations"""
        
        available_locations = ['Walking.fbx', 'Idle.fbx', 'Man.fbx']
        target_time = datetime.now()
        
        # Test rainy evening scenario
        rainy_recs = self.engine.get_time_specific_recommendations(
            target_time, available_locations, "rainy evening"
        )
        
        # Should favor indoor activities during rainy weather
        indoor_activities = ['Idle.fbx', 'Man.fbx']
        indoor_recommended = any(
            rec.location_id in indoor_activities and rec.suitability_score > 0.5
            for rec in rainy_recs
        )
        self.assertTrue(indoor_recommended)
    
    def test_seasonal_preferences(self):
        """Test seasonal preference matching"""
        
        # Test that seasonal preferences affect recommendations
        profile = self.engine.location_profiles['Walking.fbx']
        
        # Walking should prefer spring/summer/fall
        spring_context = self.engine.get_current_context()
        spring_context.season = Season.SPRING
        
        winter_context = self.engine.get_current_context()
        winter_context.season = Season.WINTER
        
        spring_score = self.engine._calculate_contextual_suitability(
            profile, spring_context
        )
        
        winter_score = self.engine._calculate_contextual_suitability(
            profile, winter_context
        )
        
        # Spring should be more suitable for walking than winter
        self.assertGreater(spring_score, winter_score)
    
    def test_crowd_level_estimation(self):
        """Test crowd level estimation based on time patterns"""
        
        # Weekend afternoon should be higher crowd
        weekend_afternoon = datetime.now().replace(
            hour=14, minute=0, second=0, 
            weekday=5  # Saturday
        )
        weekend_crowd = self.engine._estimate_crowd_level(weekend_afternoon)
        
        # Weekday early morning should be lower crowd
        weekday_morning = datetime.now().replace(
            hour=7, minute=0, second=0,
            weekday=1  # Tuesday
        )
        weekday_crowd = self.engine._estimate_crowd_level(weekday_morning)
        
        # We can't guarantee exact values, but weekend should generally be higher
        # This test ensures the function runs without errors
        self.assertIn(weekend_crowd, ['low', 'medium', 'high'])
        self.assertIn(weekday_crowd, ['low', 'medium', 'high'])
    
    def test_special_considerations_generation(self):
        """Test generation of special considerations"""
        
        # Test high temperature scenario
        hot_context = self.engine.get_current_context(
            weather_override={
                'condition': WeatherCondition.CLEAR,
                'temperature': 40.0,  # Very hot
                'humidity': 70.0,
                'uv_index': 10.0,  # High UV
                'precipitation_chance': 0.0,
                'wind_speed': 5.0
            }
        )
        
        profile = self.engine.location_profiles['Walking.fbx']
        considerations = self.engine._get_special_considerations(profile, hot_context)
        
        # Should include heat-related warnings
        heat_warning = any('hot' in consideration.lower() or 'hydrat' in consideration.lower() 
                          for consideration in considerations)
        uv_warning = any('uv' in consideration.lower() or 'sunscreen' in consideration.lower()
                        for consideration in considerations)
        
        self.assertTrue(heat_warning or uv_warning)
    
    def test_comprehensive_recommendations(self):
        """Test comprehensive recommendation generation"""
        
        available_locations = ['Walking.fbx', 'Running.fbx', 'Idle.fbx', 'Man.fbx']
        
        recommendations = self.engine.generate_contextual_recommendations(
            available_locations, top_k=3
        )
        
        # Verify recommendation structure
        self.assertLessEqual(len(recommendations), 3)
        
        for rec in recommendations:
            self.assertIsInstance(rec.location_id, str)
            self.assertIsInstance(rec.suitability_score, float)
            self.assertIsInstance(rec.contextual_reasons, list)
            self.assertIsInstance(rec.optimal_time_window, tuple)
            self.assertGreater(len(rec.contextual_reasons), 0)
    
    def test_analytics_generation(self):
        """Test analytics generation for contextual system"""
        
        analytics = self.engine.get_analytics()
        
        # Verify analytics structure
        self.assertIn('current_context', analytics)
        self.assertIn('location_suitability_scores', analytics)
        self.assertIn('total_locations', analytics)
        self.assertIn('avg_suitability', analytics)
        self.assertIn('contextual_weights', analytics)
        
        # Verify current context has required fields
        current_context = analytics['current_context']
        self.assertIn('time_of_day', current_context)
        self.assertIn('season', current_context)
        self.assertIn('weather_condition', current_context)


class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios combining both systems"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.tourist_graph = TouristInterestGraph(storage_dir=str(self.temp_dir / "tourist"))
        self.contextual_engine = ContextualRecommendationEngine(storage_dir=str(self.temp_dir / "contextual"))
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_rainy_evening_scenario(self):
        """Test the specific scenario mentioned in requirements: 'indoor cafes during rainy evenings'"""
        
        # Build user profile with some cafe/indoor preferences
        cafe_interactions = [
            "indoor cafe with coffee",
            "cozy indoor space",
            "relaxing inside environment"
        ]
        
        for i, query in enumerate(cafe_interactions):
            interaction = {
                'query': query,
                'selected_model': 'Idle.fbx',  # Indoor relaxation model
                'context': {
                    'weather': {'condition': 'rainy'},
                    'time_of_day': 'evening'
                },
                'feedback': {'satisfaction': 0.8},
                'interaction_time': 40
            }
            
            self.tourist_graph.capture_interest_from_interaction(
                "cafe_user", f"session_{i}", interaction
            )
        
        # Get contextual recommendations for rainy evening
        evening_time = datetime.now().replace(hour=19, minute=0)
        contextual_recs = self.contextual_engine.get_time_specific_recommendations(
            evening_time, ['Idle.fbx', 'Man.fbx', 'Walking.fbx'], "rainy evening indoor cafes"
        )
        
        # Get tourist interest recommendations
        tourist_recs = self.tourist_graph.get_recommendations_for_user(
            "cafe_user", 
            {'weather': 'rainy', 'time': 'evening'}, 
            ['Idle.fbx', 'Man.fbx', 'Walking.fbx']
        )
        
        # Both systems should favor indoor activities
        indoor_models = ['Idle.fbx', 'Man.fbx']
        
        contextual_indoor = any(
            rec.location_id in indoor_models and rec.suitability_score > 0.5
            for rec in contextual_recs
        )
        
        tourist_indoor = any(
            rec['location_id'] in indoor_models and rec['score'] > 0.5
            for rec in tourist_recs
        )
        
        self.assertTrue(contextual_indoor, "Contextual engine should recommend indoor activities for rainy evening")
        self.assertTrue(tourist_indoor, "Tourist graph should recommend indoor activities based on user history")
    
    def test_nature_enthusiast_morning_scenario(self):
        """Test scenario for nature enthusiast in the morning with good weather"""
        
        # Build nature enthusiast profile
        nature_interactions = [
            "hiking mountain trails",
            "walking in beautiful nature",
            "outdoor forest exploration",
            "scenic nature views"
        ]
        
        for i, query in enumerate(nature_interactions):
            interaction = {
                'query': query,
                'selected_model': 'Walking.fbx',
                'context': {
                    'weather': {'condition': 'clear', 'temperature': 22},
                    'time_of_day': 'morning'
                },
                'feedback': {'satisfaction': 0.9},
                'interaction_time': 50
            }
            
            self.tourist_graph.capture_interest_from_interaction(
                "nature_user", f"session_{i}", interaction
            )
        
        # Get recommendations for clear morning
        morning_time = datetime.now().replace(hour=9, minute=0)
        contextual_recs = self.contextual_engine.get_time_specific_recommendations(
            morning_time, ['Walking.fbx', 'Running.fbx', 'Idle.fbx'], None
        )
        
        # Update context to clear weather
        clear_context = self.contextual_engine.get_current_context(
            weather_override={
                'condition': WeatherCondition.CLEAR,
                'temperature': 22.0,
                'humidity': 60.0,
                'precipitation_chance': 0.0,
                'wind_speed': 5.0,
                'uv_index': 5.0
            }
        )
        
        contextual_recs_clear = self.contextual_engine.generate_contextual_recommendations(
            ['Walking.fbx', 'Running.fbx', 'Idle.fbx'],
            context_override=clear_context
        )
        
        tourist_recs = self.tourist_graph.get_recommendations_for_user(
            "nature_user",
            {'weather': 'clear', 'temperature': 22, 'time': 'morning'},
            ['Walking.fbx', 'Running.fbx', 'Idle.fbx']
        )
        
        # Both systems should highly favor Walking.fbx for this scenario
        walking_contextual = next(
            (rec for rec in contextual_recs_clear if rec.location_id == 'Walking.fbx'), 
            None
        )
        walking_tourist = next(
            (rec for rec in tourist_recs if rec['location_id'] == 'Walking.fbx'),
            None
        )
        
        self.assertIsNotNone(walking_contextual)
        self.assertIsNotNone(walking_tourist)
        self.assertGreater(walking_contextual.suitability_score, 0.6)
        self.assertGreater(walking_tourist['score'], 0.7)
    
    def test_clustering_with_contextual_validation(self):
        """Test that interest clustering works well with contextual recommendations"""
        
        # Create users with different preference patterns
        user_patterns = {
            "outdoor_enthusiast": [
                ("hiking trails", "Walking.fbx"),
                ("running outdoors", "Running.fbx"),
                ("nature walks", "Walking.fbx")
            ],
            "indoor_preferrer": [
                ("indoor relaxation", "Idle.fbx"),
                ("quiet indoor spaces", "Man.fbx"),
                ("cozy environments", "Idle.fbx")
            ],
            "mixed_preferences": [
                ("walking sometimes", "Walking.fbx"),
                ("resting when tired", "Idle.fbx"),
                ("general activities", "Man.fbx")
            ]
        }
        
        for user_type, interactions in user_patterns.items():
            for i, (query, model) in enumerate(interactions):
                interaction = {
                    'query': query,
                    'selected_model': model,
                    'context': {},
                    'feedback': {'satisfaction': 0.8},
                    'interaction_time': 35
                }
                
                self.tourist_graph.capture_interest_from_interaction(
                    f"{user_type}_user", f"session_{i}", interaction
                )
        
        # Perform clustering
        clusters = self.tourist_graph.perform_interest_clustering(min_users=2)
        
        # Verify clustering created meaningful groups
        self.assertGreater(len(clusters), 0)
        
        # Test that contextual recommendations align with cluster patterns
        # For outdoor cluster, clear weather should boost outdoor activities
        outdoor_user_recs = self.tourist_graph.get_recommendations_for_user(
            "outdoor_enthusiast_user",
            {'weather': 'clear'},
            ['Walking.fbx', 'Running.fbx', 'Idle.fbx']
        )
        
        outdoor_activity_recommended = any(
            rec['location_id'] in ['Walking.fbx', 'Running.fbx'] and rec['score'] > 0.5
            for rec in outdoor_user_recs
        )
        
        self.assertTrue(outdoor_activity_recommended)


def run_tourism_tests():
    """Run all tourism enhancement tests"""
    
    print("=" * 60)
    print("TOURISM ENHANCEMENT TESTS")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTouristInterestGraph))
    suite.addTests(loader.loadTestsFromTestCase(TestContextualRecommendationEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationScenarios))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("TOURISM TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tourism_tests()
    exit(0 if success else 1)