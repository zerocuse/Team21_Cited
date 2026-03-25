from flask import Blueprint, jsonify
from models.credibility_calculator import CredibilityCalculator
from models.source_reputation import SourceReputation
from models.fact_comparison_engine import FactComparisonEngine

claim_results_bp = Blueprint('claim_results', __name__)

@claim_results_bp.route('/api/claim/<claim_id>/result', methods=['GET'])
def get_claim_result(claim_id):
	if not claim_id:
		return jsonify({"error": "Claim ID is required"}), 400

	try:
		credibility = CredibilityCalculator()
		reputation = SourceReputation()
		comparison = FactComparisonEngine()

		credibility_score = credibility.calculate(claim_id)
		reputation_score = reputation.get_score(claim_id)
		contradiction = comparison.detect_contradiction(claim_id)

		if credibility_score >= 70:
			label = "High"
		elif credibility_score >= 40:
			label = "Medium"
		else:
			label = "Low"

		return jsonify({
			"claim_id": claim_id,
			"credibility_score": credibility_score,
			"credibility_label": label,
			"source_reputation": reputation_score,
			"contradiction_detected": contradiction
		}), 200

	except Exception:
		return jsonify({"error": "Claim not found"}), 404