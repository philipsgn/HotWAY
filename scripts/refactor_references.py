"""
Refactor script to safely update legacy references from binhthanh/hanggon to standard/urban graphs.
"""
from pathlib import Path

# 1. adaptive_routing_env.py
p1 = Path('src/envs/adaptive_routing_env.py')
c = p1.read_text(encoding='utf-8')
c = c.replace('binhthanh_routing_subgraph.pickle', 'urban_routing_subgraph.pickle')
p1.write_text(c, encoding='utf-8')

# 2. routing_env.py
p2 = Path('src/envs/routing_env.py')
c = p2.read_text(encoding='utf-8')
c = c.replace('binhthanh_routing_subgraph.pickle', 'urban_routing_subgraph.pickle')
p2.write_text(c, encoding='utf-8')

# 3. road_matrix.py
p3 = Path('src/services/road_matrix.py')
c = p3.read_text(encoding='utf-8')
c = c.replace('data/binhthanh_graph.pickle', 'data/hcmc_compact_graph.pickle')
c = c.replace('region = "binhthanh"', 'region = "hcmc_compact"')
p3.write_text(c, encoding='utf-8')

# 4. dispatch.py
p4 = Path('backend/app/api/dispatch.py')
c = p4.read_text(encoding='utf-8')
c = c.replace('ord_binhthanh_sample_01', 'ord_sample_01')
p4.write_text(c, encoding='utf-8')

# 5. spatial.py
p5 = Path('backend/app/api/spatial.py')
c = p5.read_text(encoding='utf-8')
c = c.replace('data/binhthanh_roads.geojson', 'data/hcmc_compact_roads.geojson')
c = c.replace('data/hanggon_roads.geojson', 'data/hcmc_compact_roads.geojson')
c = c.replace('data/binhthanh_buildings.geojson', 'data/buildings.geojson')
c = c.replace('data/hanggon_buildings.geojson', 'data/buildings.geojson')
p5.write_text(c, encoding='utf-8')

# 6. config.py
p6 = Path('backend/app/core/config.py')
c = p6.read_text(encoding='utf-8')
c = c.replace('data/binhthanh_graph.graphml', 'data/hcmc_compact_graph.graphml')
p6.write_text(c, encoding='utf-8')

# 7. rl_inference_service.py
p7 = Path('backend/app/services/rl_inference_service.py')
c = p7.read_text(encoding='utf-8')
c = c.replace('data/hanggon_graph.graphml', 'data/hcmc_compact_graph.graphml')
p7.write_text(c, encoding='utf-8')

# 8. routing_service.py
p8 = Path('backend/app/services/routing_service.py')
c = p8.read_text(encoding='utf-8')
c = c.replace('data/binhthanh_graph.graphml', 'data/hcmc_compact_graph.graphml')
c = c.replace('data/hanggon_graph.graphml', 'data/hcmc_compact_graph.graphml')
c = c.replace('"binhthanh_benchmark_routes"', '"vietnam_benchmark_routes"')
p8.write_text(c, encoding='utf-8')

print('Refactored all references successfully!')

