"""
Connecteurs de sourcing par institution.

Chaque module (met, rijksmuseum, bhl) expose une fonction `search` qui produit
des `SourcingRecord` au format normalisé consommable par :
  - le scoring_agent.py local
  - l'API /api/works du cockpit (web/lib/works.ts)

Le format normalisé est défini dans base.py.
"""
