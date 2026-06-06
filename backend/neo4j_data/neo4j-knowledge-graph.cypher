// ============================================
// 水库质量监测系统 · Neo4j 知识图谱模拟数据
// 用途：Neo4j Browser 手动调试用
// 注意：水库/站点/指标节点由系统启动时自动从 MySQL 同步
//       本脚本仅创建静态种子数据（河流 + 污染源 + 关系）
// ============================================

// ---- 创建约束 ----
CREATE CONSTRAINT IF NOT EXISTS FOR (r:Reservoir) REQUIRE r.code IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (s:MonitoringStation) REQUIRE s.code IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (r:River) REQUIRE r.name IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (p:PollutionSource) REQUIRE p.name IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (i:Indicator) REQUIRE i.code IS UNIQUE;

// ---- 河流节点 ----
CREATE (:River {name: '史河', length: 220, watershed: '淮河流域'});
CREATE (:River {name: '淠河', length: 253, watershed: '淮河流域'});
CREATE (:River {name: '杭埠河', length: 145, watershed: '长江流域'});
CREATE (:River {name: '南淝河', length: 60, watershed: '淮河流域'});
CREATE (:River {name: '滁河', length: 269, watershed: '长江流域'});
CREATE (:River {name: '青弋江', length: 291, watershed: '长江流域'});

// ---- 河流流入水库关系 ----
// 对齐实际水库 code：QLS-001(青龙山)、MSH-002(梅山)、LHK-003(龙河口)、DPS-004(董铺)
MATCH (r:River {name: '史河'}), (res:Reservoir {code: 'MSH-002'}) CREATE (r)-[:FLOWS_INTO {distance_km: 0}]->(res);
MATCH (r:River {name: '杭埠河'}), (res:Reservoir {code: 'LHK-003'}) CREATE (r)-[:FLOWS_INTO]->(res);
MATCH (r:River {name: '南淝河'}), (res:Reservoir {code: 'DPS-004'}) CREATE (r)-[:FLOWS_INTO]->(res);

// ---- 污染源节点 ----
CREATE (:PollutionSource {name: '青龙山养猪场', type: '养殖场', longitude: 118.518, latitude: 32.158, risk_level: '中', violation_count: 2});
CREATE (:PollutionSource {name: '梅山化工厂', type: '工业企业', longitude: 118.328, latitude: 32.095, risk_level: '高', violation_count: 5});
CREATE (:PollutionSource {name: '董铺农田径流区', type: '农业面源', longitude: 117.160, latitude: 31.910, risk_level: '中', violation_count: null});
CREATE (:PollutionSource {name: '龙河口采砂场', type: '其他', longitude: 117.950, latitude: 31.755, risk_level: '低', violation_count: 0});

// ---- 污染源排入河流关系 ----
MATCH (p:PollutionSource {name: '青龙山养猪场'}), (r:River {name: '史河'}) CREATE (p)-[:DISCHARGES_INTO {distance_km: 0.8}]->(r);
MATCH (p:PollutionSource {name: '梅山化工厂'}), (r:River {name: '史河'}) CREATE (p)-[:DISCHARGES_INTO {distance_km: 0.3}]->(r);
MATCH (p:PollutionSource {name: '董铺农田径流区'}), (r:River {name: '南淝河'}) CREATE (p)-[:DISCHARGES_INTO {distance_km: 1.2}]->(r);
MATCH (p:PollutionSource {name: '龙河口采砂场'}), (r:River {name: '杭埠河'}) CREATE (p)-[:DISCHARGES_INTO {distance_km: 0.2}]->(r);

// ---- 指标关联关系 ----
// 对齐实际指标 code：ph(酸碱度)、rjy(溶解氧)、cod(化学需氧量)、ad(氨氮)、swt(水温)、zd(浊度)
MATCH (a:Indicator {code: 'ad'}), (b:Indicator {code: 'rjy'}) CREATE (a)-[:CORRELATED_WITH {type: 'negative', strength: 0.65, description: '氨氮升高消耗溶解氧'}]->(b);
MATCH (a:Indicator {code: 'swt'}), (b:Indicator {code: 'ad'}) CREATE (a)-[:CORRELATED_WITH {type: 'positive', strength: 0.55, description: '水温升高促进底泥氮释放'}]->(b);
MATCH (a:Indicator {code: 'ad'}), (b:Indicator {code: 'cod'}) CREATE (a)-[:CORRELATED_WITH {type: 'positive', strength: 0.6, description: '氨氮与化学需氧量同源（有机物污染）'}]->(b);
MATCH (a:Indicator {code: 'zd'}), (b:Indicator {code: 'cod'}) CREATE (a)-[:CORRELATED_WITH {type: 'positive', strength: 0.5, description: '浊度升高常伴随有机物增加'}]->(b);

// ---- 污染溯源查询示例 ----
// 查询：从董铺水库氨氮超标出发，向上游追溯污染源
// MATCH (res:Reservoir {code: 'DPS-004'})<-[f:FLOWS_INTO]-(r:River)<-[d:DISCHARGES_INTO]-(p:PollutionSource)
// RETURN res.name, r.name, p.name, p.type, p.risk_level, p.violation_count, d.distance_km
// ORDER BY p.risk_level DESC, p.violation_count DESC;
