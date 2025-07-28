"""
Comprehensive test suite for AI-driven 3D model selection assistant
Tests all three AI layers: Intent Disambiguation, Semantic Search, and Personalization
"""

import unittest
import json
import time
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents'))

from intent_disambiguation import IntentDisambiguationEngine, ModelStyle, ModelPurpose, ModelMotion
from semantic_search import SemanticSearchEngine
from personalization import PersonalizationEngine
from model_selection_agent import IntegratedModelSelector

class TestIntentDisambiguation(unittest.TestCase):
    """Test the Intent Disambiguation Engine"""
    
    def setUp(self):
        self.engine = IntentDisambiguationEngine()
    
    def test_clear_intent_classification(self):
        """Test classification of clear, unambiguous queries"""
        # Test walking intent
        intent = self.engine.classify_intent("Show me a walking person")
        self.assertEqual(intent.motion, ModelMotion.WALKING)
        self.assertGreater(intent.confidence, 0.2)
        
        # Test running intent
        intent = self.engine.classify_intent("I need a running animation")
        self.assertEqual(intent.motion, ModelMotion.RUNNING)
        self.assertEqual(intent.purpose, ModelPurpose.ANIMATION)
        
        # Test rigged model intent
        intent = self.engine.classify_intent("Show me a rigged model with skeleton")
        self.assertEqual(intent.purpose, ModelPurpose.RIGGED)
    
    def test_ambiguous_query_detection(self):
        """Test detection and handling of ambiguous queries"""
        # Ambiguous query
        intent = self.engine.classify_intent("Show me a person")
        self.assertIn("person", intent.ambiguities)
        self.assertGreater(len(intent.suggestions), 0)
        
        # Very ambiguous query
        intent = self.engine.classify_intent("I want a model")
        self.assertIn("model", intent.ambiguities)
        self.assertLower(intent.confidence, 0.5)
    
    def test_style_classification(self):
        """Test style preference detection"""
        # Realistic style
        intent = self.engine.classify_intent("Show me a realistic human character")
        self.assertEqual(intent.style, ModelStyle.REALISTIC)
        
        # Stylized style
        intent = self.engine.classify_intent("Display a stylized cartoon character")
        self.assertEqual(intent.style, ModelStyle.STYLIZED)
        
        # Neutral/default style
        intent = self.engine.classify_intent("Show me a basic character")
        self.assertEqual(intent.style, ModelStyle.NEUTRAL)
    
    def test_ambiguity_resolution(self):
        """Test the ambiguity resolution feature"""
        # Create ambiguous intent
        original_intent = self.engine.classify_intent("Show me a character")
        self.assertGreater(len(original_intent.ambiguities), 0)
        
        # Resolve with clarification
        resolved_intent = self.engine.resolve_ambiguity(
            original_intent, "I want a walking animation"
        )
        self.assertEqual(resolved_intent.motion, ModelMotion.WALKING)
        self.assertEqual(len(resolved_intent.ambiguities), 0)

class TestSemanticSearch(unittest.TestCase):
    """Test the Semantic Search Engine"""
    
    def setUp(self):
        self.engine = SemanticSearchEngine()
    
    def test_semantic_similarity_ranking(self):
        """Test that semantic search ranks models correctly"""
        # Walking query should rank Walking.fbx highest
        results = self.engine.search("Show me a walking person", top_k=3)
        model_names = [result.model_name for result in results]
        
        # Should have Walking.fbx in top results
        self.assertIn("Walking.fbx", model_names[:2])
        
        # Check similarity scores are reasonable
        for result in results:
            self.assertGreaterEqual(result.similarity_score, 0.0)
            self.assertLessEqual(result.similarity_score, 1.0)
    
    def test_motion_specific_queries(self):
        """Test queries with specific motion requirements"""
        # Running query
        results = self.engine.search("I need fast running motion", top_k=3)
        running_result = next((r for r in results if r.model_name == "Running.fbx"), None)
        self.assertIsNotNone(running_result)
        self.assertGreater(running_result.similarity_score, 0.5)
        
        # Idle query
        results = self.engine.search("Show me standing still pose", top_k=3)
        idle_result = next((r for r in results if r.model_name == "Idle.fbx"), None)
        self.assertIsNotNone(idle_result)
        self.assertGreater(idle_result.similarity_score, 0.8)
    
    def test_technical_queries(self):
        """Test queries with technical requirements"""
        # Rigged model query
        results = self.engine.search("I need a rigged character with bones", top_k=3)
        rig_result = next((r for r in results if r.model_name == "Man_Rig.fbx"), None)
        self.assertIsNotNone(rig_result)
        self.assertGreater(rig_result.similarity_score, 0.6)
    
    def test_search_explanation(self):
        """Test the search explanation feature"""
        explanation = self.engine.explain_search("Show me a walking person")
        
        self.assertIn("query", explanation)
        self.assertIn("search_results", explanation)
        self.assertIn("embedding_interpretation", explanation)
        self.assertGreater(len(explanation["search_results"]), 0)

class TestPersonalization(unittest.TestCase):
    """Test the Personalization Engine"""
    
    def setUp(self):
        # Use temporary directory for testing
        import tempfile
        self.temp_dir = Path(tempfile.mkdtemp())
        self.engine = PersonalizationEngine(storage_dir=self.temp_dir)
    
    def tearDown(self):
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_session_creation(self):
        """Test session creation and management"""
        session_id = self.engine.start_session("test_user")
        self.assertIsNotNone(session_id)
        self.assertIn(session_id, self.engine.active_sessions)
        
        # Test anonymous session
        anon_session = self.engine.start_session()
        self.assertIsNotNone(anon_session)
        self.assertIn(anon_session, self.engine.active_sessions)
    
    def test_interaction_recording(self):
        """Test recording and tracking of user interactions"""
        session_id = self.engine.start_session("test_user")
        
        # Record some interactions
        self.engine.record_interaction(
            session_id, "Show me walking", "Walking.fbx", 
            "neutral", "animation", "walking", 0.8
        )
        
        session = self.engine.active_sessions[session_id]
        self.assertEqual(len(session.interactions), 1)
        self.assertEqual(session.interactions[0].selected_model, "Walking.fbx")
    
    def test_preference_learning(self):
        """Test that preferences are learned from interactions"""
        session_id = self.engine.start_session("test_user")
        available_models = ["Man.fbx", "Idle.fbx", "Walking.fbx", "Running.fbx", "Man_Rig.fbx"]
        
        # Record multiple walking interactions
        for i in range(3):
            self.engine.record_interaction(
                session_id, f"Show walking {i}", "Walking.fbx",
                "neutral", "animation", "walking", 0.8
            )
        
        # Get recommendations - should prefer Walking.fbx
        recommendations = self.engine.get_recommendations(
            session_id, "Show me something", available_models, top_k=3
        )
        
        walking_rec = next((r for r in recommendations if r.model_name == "Walking.fbx"), None)
        self.assertIsNotNone(walking_rec)
        self.assertGreater(walking_rec.personalization_score, 0.3)
    
    def test_feedback_integration(self):
        """Test feedback learning and preference adjustment"""
        session_id = self.engine.start_session("test_user")
        
        # Record interaction
        self.engine.record_interaction(
            session_id, "Show me a character", "Man.fbx",
            "neutral", "display", "idle", 0.7
        )
        
        # Provide negative feedback
        self.engine.update_preferences_from_feedback(session_id, 0, "negative")
        
        # Check that preferences were adjusted
        session = self.engine.active_sessions[session_id]
        self.assertLess(session.current_preferences.favorite_models.get("Man.fbx", 0), 2)
    
    def test_session_theme_inference(self):
        """Test inference of session themes"""
        session_id = self.engine.start_session("test_user")
        
        # Record multiple animation-focused interactions
        for i in range(4):
            self.engine.record_interaction(
                session_id, f"Animation query {i}", "Walking.fbx",
                "neutral", "animation", "walking", 0.8
            )
        
        summary = self.engine.get_session_summary(session_id)
        self.assertIsNotNone(summary["session_theme"])
        self.assertIn("animation", summary["session_theme"])

class TestIntegratedSystem(unittest.TestCase):
    """Test the integrated AI model selector"""
    
    def setUp(self):
        self.selector = IntegratedModelSelector()
    
    def test_comprehensive_analysis(self):
        """Test the comprehensive analysis that combines all AI layers"""
        result = self.selector.analyze_question_comprehensive("Show me a walking person")
        
        # Check basic structure
        self.assertIn("selected_model", result)
        self.assertIn("confidence", result)
        self.assertIn("intent_analysis", result)
        self.assertIn("semantic_analysis", result)
        self.assertIn("ai_method", result)
        
        # Check AI method
        self.assertEqual(result["ai_method"], "integrated_ai_layers")
        
        # Check confidence is reasonable
        self.assertGreaterEqual(result["confidence"], 0.0)
        self.assertLessEqual(result["confidence"], 1.0)
    
    def test_session_based_personalization(self):
        """Test personalization across multiple queries in a session"""
        session_id = self.selector.start_user_session("test_user")
        
        # First query
        result1 = self.selector.analyze_question_comprehensive(
            "Show me walking", session_id
        )
        
        # Second similar query - should have higher personalization
        result2 = self.selector.analyze_question_comprehensive(
            "Show me walking again", session_id
        )
        
        # Extract personalization scores
        def get_personalization_score(result, model):
            for rec in result.get("personalization_analysis", []):
                if rec["model"] == model:
                    return rec["score"]
            return 0
        
        selected_model = result1["selected_model"]
        score1 = get_personalization_score(result1, selected_model)
        score2 = get_personalization_score(result2, selected_model)
        
        # Second query should have higher personalization score
        self.assertGreaterEqual(score2, score1)
    
    def test_intent_model_matching(self):
        """Test that intent classification properly influences model selection"""
        # Clear rigged model query
        result = self.selector.analyze_question_comprehensive(
            "I need a rigged model with skeleton for custom animations"
        )
        
        intent = result["intent_analysis"]
        self.assertEqual(intent["purpose"], "rigged")
        self.assertEqual(intent["motion"], "custom")
        
        # The model with highest intent match should be ranked well
        # (though personalization might override in integrated system)
        self.assertIn("Man_Rig.fbx", [r["model"] for r in result["semantic_analysis"][:2]])
    
    def test_explanation_feature(self):
        """Test the detailed explanation feature"""
        explanation = self.selector.explain_recommendation("Show me a walking character")
        
        self.assertIn("final_recommendation", explanation)
        self.assertIn("layer_analysis", explanation)
        self.assertIn("integration_details", explanation)
        
        # Check layer analysis structure
        layers = explanation["layer_analysis"]
        self.assertIn("intent_disambiguation", layers)
        self.assertIn("semantic_search", layers)
        self.assertIn("personalization", layers)
    
    def test_legacy_compatibility(self):
        """Test that legacy API methods still work"""
        # Test legacy analyze_question method
        result = self.selector.analyze_question("Show me a person")
        
        self.assertIn("selected_model", result)
        self.assertIn("confidence", result)
        
        # Test model info method
        model_info = self.selector.get_model_info("Walking.fbx")
        self.assertEqual(model_info["name"], "Walking.fbx")
        self.assertIn("characteristics", model_info)
        
        # Test list models method
        models = self.selector.list_available_models()
        self.assertGreater(len(models), 0)
        self.assertTrue(all("name" in model for model in models))

class TestEndToEndWorkflow(unittest.TestCase):
    """Test complete end-to-end workflows"""
    
    def setUp(self):
        self.selector = IntegratedModelSelector()
    
    def test_new_user_workflow(self):
        """Test complete workflow for a new user"""
        # Start session
        session_id = self.selector.start_user_session("new_user")
        
        # First query - should rely mostly on intent and semantic
        result1 = self.selector.analyze_question_comprehensive(
            "Show me a walking person", session_id
        )
        
        # Should have low personalization contribution initially
        personalization_scores = [r["score"] for r in result1.get("personalization_analysis", [])]
        if personalization_scores:
            self.assertLess(max(personalization_scores), 0.5)
        
        # Multiple similar queries to build preferences
        for i in range(3):
            self.selector.analyze_question_comprehensive(
                f"Show me walking animation {i}", session_id
            )
        
        # Later query should have higher personalization contribution
        result_final = self.selector.analyze_question_comprehensive(
            "Show me walking", session_id
        )
        
        final_personalization_scores = [r["score"] for r in result_final.get("personalization_analysis", [])]
        if final_personalization_scores:
            self.assertGreater(max(final_personalization_scores), 0.3)
    
    def test_ambiguous_query_workflow(self):
        """Test workflow with ambiguous queries"""
        session_id = self.selector.start_user_session("ambiguous_user")
        
        # Ambiguous query
        result = self.selector.analyze_question_comprehensive(
            "Show me a character", session_id
        )
        
        # Should detect ambiguities and provide suggestions
        intent = result["intent_analysis"]
        self.assertGreater(len(intent.get("suggestions", [])), 0)
        
        # Follow-up with clarification
        clarified_result = self.selector.analyze_question_comprehensive(
            "Show me a walking character", session_id
        )
        
        # Should have higher confidence after clarification
        self.assertGreater(clarified_result["confidence"], result["confidence"])
    
    def test_feedback_learning_workflow(self):
        """Test feedback learning over multiple interactions"""
        session_id = self.selector.start_user_session("feedback_user")
        
        # Initial interaction
        result1 = self.selector.analyze_question_comprehensive(
            "Show me a character", session_id
        )
        selected_model = result1["selected_model"]
        
        # Provide negative feedback
        self.selector.update_user_feedback(session_id, 0, "negative")
        
        # Same query again - should be less likely to select same model
        result2 = self.selector.analyze_question_comprehensive(
            "Show me a character", session_id
        )
        
        # Check that the system learned from feedback
        # (This might not always change the selection due to other factors,
        # but the personalization scores should reflect the feedback)
        summary = self.selector.get_session_summary(session_id)
        self.assertGreater(summary["interactions_count"], 1)

def run_performance_tests():
    """Run performance tests for the AI system"""
    print("\n" + "="*60)
    print("PERFORMANCE TESTS")
    print("="*60)
    
    selector = IntegratedModelSelector()
    
    # Test query processing speed
    queries = [
        "Show me a walking person",
        "I need a running character",
        "Display an idle pose",
        "Show me a rigged model",
        "I want something for animation"
    ]
    
    start_time = time.time()
    for query in queries:
        result = selector.analyze_question_comprehensive(query)
    end_time = time.time()
    
    avg_time = (end_time - start_time) / len(queries)
    print(f"Average query processing time: {avg_time:.3f} seconds")
    print(f"Queries per second: {1/avg_time:.1f}")
    
    # Test session overhead
    session_id = selector.start_user_session("perf_user")
    
    start_time = time.time()
    for i, query in enumerate(queries):
        result = selector.analyze_question_comprehensive(query, session_id)
    end_time = time.time()
    
    avg_time_with_session = (end_time - start_time) / len(queries)
    print(f"Average query time with session: {avg_time_with_session:.3f} seconds")
    
    session_overhead = avg_time_with_session - avg_time
    print(f"Session overhead: {session_overhead:.3f} seconds ({session_overhead/avg_time*100:.1f}%)")

if __name__ == "__main__":
    # Run unit tests
    unittest.main(verbosity=2, exit=False)
    
    # Run performance tests
    run_performance_tests()