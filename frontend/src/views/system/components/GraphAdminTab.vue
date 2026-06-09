<template>
  <div>
    <el-tabs v-model="activeTab" class="mb-4">
      <el-tab-pane label="水库管理" name="reservoir">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-3">
            <el-select v-model="reservoirFilterWatershed" placeholder="所属流域" clearable class="w-40" @change="fetchReservoirList">
              <el-option label="淮河流域" value="淮河流域" />
              <el-option label="长江流域" value="长江流域" />
            </el-select>
          </div>
          <el-button type="primary" @click="openReservoirDialog()">
            <el-icon><Plus /></el-icon>新增水库
          </el-button>
        </div>
        <el-table v-loading="reservoirLoading" :data="reservoirList" border stripe class="w-full">
          <el-table-column prop="code" label="编号" width="100" />
          <el-table-column prop="name" label="名称" min-width="140" />
          <el-table-column prop="location" label="位置" width="160" show-overflow-tooltip />
          <el-table-column prop="water_grade" label="水质等级" width="80" align="center" />
          <el-table-column prop="watershed" label="流域" width="100" />
          <el-table-column prop="capacity" label="库容" width="80" align="right" />
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click="openReservoirDialog(row)">编辑</el-button>
              <el-button type="danger" link size="small" @click="handleDeleteReservoir(row)">删除</el-button>
            </template>
          </el-table-column>
          <template #empty><el-empty description="暂无水库数据" /></template>
        </el-table>
        <div class="flex justify-end mt-4">
          <el-pagination v-model:current-page="reservoirPagination.page" v-model:page-size="reservoirPagination.page_size" :total="reservoirPagination.total" :page-sizes="[10,20,50]" layout="total, sizes, prev, pager, next, jumper" background @size-change="()=>{reservoirPagination.page=1;fetchReservoirList()}" @current-change="fetchReservoirList" />
        </div>
        <el-dialog v-model="reservoirDialogVisible" :title="reservoirEditMode?'编辑水库':'新增水库'" width="600px" :close-on-click-modal="false" @close="resetReservoirForm">
          <el-form ref="reservoirFormRef" :model="reservoirForm" :rules="reservoirFormRules" label-width="100px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="水库编号" prop="code">
                  <el-input v-model="reservoirForm.code" placeholder="如 QLS-001" :disabled="reservoirEditMode" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="水库名称" prop="name">
                  <el-input v-model="reservoirForm.name" placeholder="请输入名称" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="所在位置" prop="location">
              <el-input v-model="reservoirForm.location" placeholder="选填" />
            </el-form-item>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="经度" prop="longitude">
                  <el-input v-model="reservoirForm.longitude" placeholder="选填" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="纬度" prop="latitude">
                  <el-input v-model="reservoirForm.latitude" placeholder="选填" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="库容(万m³)" prop="capacity">
                  <el-input v-model="reservoirForm.capacity" placeholder="选填" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="水质等级" prop="water_grade">
                  <el-select v-model="reservoirForm.water_grade" placeholder="选填" clearable class="w-full">
                    <el-option label="Ⅰ类" value="Ⅰ类" />
                    <el-option label="Ⅱ类" value="Ⅱ类" />
                    <el-option label="Ⅲ类" value="Ⅲ类" />
                    <el-option label="Ⅳ类" value="Ⅳ类" />
                    <el-option label="Ⅴ类" value="Ⅴ类" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="所属流域" prop="watershed">
              <el-select v-model="reservoirForm.watershed" placeholder="选填" clearable class="w-full">
                <el-option label="淮河流域" value="淮河流域" />
                <el-option label="长江流域" value="长江流域" />
              </el-select>
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="reservoirDialogVisible=false">取消</el-button>
            <el-button type="primary" :loading="reservoirSubmitLoading" @click="handleReservoirSubmit">{{ reservoirEditMode?'保 存':'确 定' }}</el-button>
          </template>
        </el-dialog>
      </el-tab-pane>

      <el-tab-pane label="监测站点管理" name="station">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-3">
            <el-select v-model="stationFilterType" placeholder="站点类型" clearable class="w-40" @change="fetchStationList">
              <el-option label="自动站" value="auto" />
              <el-option label="人工站" value="manual" />
              <el-option label="遥感" value="sensing" />
            </el-select>
          </div>
          <el-button type="primary" @click="openStationDialog()">
            <el-icon><Plus /></el-icon>新增站点
          </el-button>
        </div>
        <el-table v-loading="stationLoading" :data="stationList" border stripe class="w-full">
          <el-table-column prop="code" label="编号" width="110" />
          <el-table-column prop="name" label="名称" min-width="140" />
          <el-table-column prop="type" label="类型" width="80" />
          <el-table-column label="经纬度" width="200">
            <template #default="{ row }">
              <div class="flex flex-col gap-0.5">
                <div class="flex items-center gap-2"><span class="text-xs text-gray-400 shrink-0">经度</span><span class="font-mono text-sm">{{ row.longitude ?? '-' }}</span></div>
                <div class="flex items-center gap-2"><span class="text-xs text-gray-400 shrink-0">纬度</span><span class="font-mono text-sm">{{ row.latitude ?? '-' }}</span></div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="sampling_point" label="采样点" width="120" show-overflow-tooltip />
          <el-table-column prop="reservoir_code" label="所属水库" width="100" />
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click="openStationDialog(row)">编辑</el-button>
              <el-button type="danger" link size="small" @click="handleDeleteStation(row)">删除</el-button>
            </template>
          </el-table-column>
          <template #empty><el-empty description="暂无站点数据" /></template>
        </el-table>
        <div class="flex justify-end mt-4">
          <el-pagination v-model:current-page="stationPagination.page" v-model:page-size="stationPagination.page_size" :total="stationPagination.total" :page-sizes="[10,20,50]" layout="total, sizes, prev, pager, next, jumper" background @size-change="()=>{stationPagination.page=1;fetchStationList()}" @current-change="fetchStationList" />
        </div>
        <el-dialog v-model="stationDialogVisible" :title="stationEditMode?'编辑站点':'新增站点'" width="600px" :close-on-click-modal="false" @close="resetStationForm">
          <el-form ref="stationFormRef" :model="stationForm" :rules="stationFormRules" label-width="110px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="站点编号" prop="code">
                  <el-input v-model="stationForm.code" placeholder="如 QLS-A01" :disabled="stationEditMode" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="站点名称" prop="name">
                  <el-input v-model="stationForm.name" placeholder="请输入名称" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="类型" prop="type">
                  <el-select v-model="stationForm.type" placeholder="请选择" class="w-full">
                    <el-option label="自动站" value="auto" />
                    <el-option label="人工站" value="manual" />
                    <el-option label="遥感" value="sensing" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="所属水库" prop="reservoir_code">
                  <el-select v-model="stationForm.reservoir_code" placeholder="选择水库" clearable filterable class="w-full">
                    <el-option v-for="item in neo4jReservoirOptions" :key="item.code" :label="`${item.name}(${item.code})`" :value="item.code" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="经度" prop="longitude">
                  <el-input v-model="stationForm.longitude" placeholder="选填" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="纬度" prop="latitude">
                  <el-input v-model="stationForm.latitude" placeholder="选填" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="采样点位描述" prop="sampling_point">
              <el-input v-model="stationForm.sampling_point" placeholder="选填" />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="stationDialogVisible=false">取消</el-button>
            <el-button type="primary" :loading="stationSubmitLoading" @click="handleStationSubmit">{{ stationEditMode?'保 存':'确 定' }}</el-button>
          </template>
        </el-dialog>
      </el-tab-pane>

      <el-tab-pane label="监测指标管理" name="indicator">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-3">
            <el-select v-model="indicatorFilterCategory" placeholder="分类" clearable class="w-36" @change="fetchIndicatorList">
              <el-option label="物理" value="物理" />
              <el-option label="化学" value="化学" />
              <el-option label="生物" value="生物" />
              <el-option label="综合" value="综合" />
            </el-select>
          </div>
          <el-button type="primary" @click="openIndicatorDialog()">
            <el-icon><Plus /></el-icon>新增指标
          </el-button>
        </div>
        <el-table v-loading="indicatorLoading" :data="indicatorList" border stripe class="w-full">
          <el-table-column prop="code" label="编码" width="80" />
          <el-table-column prop="name" label="名称" min-width="120" />
          <el-table-column prop="unit" label="单位" width="80" />
          <el-table-column prop="category" label="分类" width="80" align="center" />
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click="openIndicatorDialog(row)">编辑</el-button>
              <el-button type="danger" link size="small" @click="handleDeleteIndicator(row)">删除</el-button>
            </template>
          </el-table-column>
          <template #empty><el-empty description="暂无指标数据" /></template>
        </el-table>
        <div class="flex justify-end mt-4">
          <el-pagination v-model:current-page="indicatorPagination.page" v-model:page-size="indicatorPagination.page_size" :total="indicatorPagination.total" :page-sizes="[10,20,50]" layout="total, sizes, prev, pager, next, jumper" background @size-change="()=>{indicatorPagination.page=1;fetchIndicatorList()}" @current-change="fetchIndicatorList" />
        </div>
        <el-dialog v-model="indicatorDialogVisible" :title="indicatorEditMode?'编辑指标':'新增指标'" width="520px" :close-on-click-modal="false" @close="resetIndicatorForm">
          <el-form ref="indicatorFormRef" :model="indicatorForm" :rules="indicatorFormRules" label-width="100px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="指标编码" prop="code">
                  <el-input v-model="indicatorForm.code" placeholder="如 DO" :disabled="indicatorEditMode" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="指标名称" prop="name">
                  <el-input v-model="indicatorForm.name" placeholder="请输入名称" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="单位" prop="unit">
                  <el-input v-model="indicatorForm.unit" placeholder="如 mg/L" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="分类" prop="category">
                  <el-select v-model="indicatorForm.category" placeholder="请选择" class="w-full">
                    <el-option label="物理" value="物理" />
                    <el-option label="化学" value="化学" />
                    <el-option label="生物" value="生物" />
                    <el-option label="综合" value="综合" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
          <template #footer>
            <el-button @click="indicatorDialogVisible=false">取消</el-button>
            <el-button type="primary" :loading="indicatorSubmitLoading" @click="handleIndicatorSubmit">{{ indicatorEditMode?'保 存':'确 定' }}</el-button>
          </template>
        </el-dialog>
      </el-tab-pane>

      <el-tab-pane label="河流管理" name="river">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-3">
            <el-select v-model="riverFilterWatershed" placeholder="所属流域" clearable class="w-40" @change="fetchRiverList">
              <el-option label="淮河流域" value="淮河流域" />
              <el-option label="长江流域" value="长江流域" />
            </el-select>
          </div>
          <el-button type="primary" @click="openRiverDialog()"><el-icon><Plus /></el-icon>新增河流</el-button>
        </div>
        <el-table v-loading="riverLoading" :data="riverList" border stripe class="w-full">
          <el-table-column prop="name" label="名称" min-width="120" />
          <el-table-column prop="length" label="长度(km)" width="100" align="right">
            <template #default="{ row }">{{ row.length ?? '-' }}</template>
          </el-table-column>
          <el-table-column prop="watershed" label="流域" width="120" />
          <el-table-column prop="flows_into_reservoir_code" label="注入水库" width="140">
            <template #default="{ row }">{{ row.flows_into_reservoir_code || '-' }}</template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click="openRiverDialog(row)">编辑</el-button>
              <el-button type="danger" link size="small" @click="handleDeleteRiver(row)">删除</el-button>
            </template>
          </el-table-column>
          <template #empty><el-empty description="暂无河流数据" /></template>
        </el-table>
        <div class="flex justify-end mt-4">
          <el-pagination v-model:current-page="riverPagination.page" v-model:page-size="riverPagination.page_size" :total="riverPagination.total" :page-sizes="[10,20,50]" layout="total, sizes, prev, pager, next, jumper" background @size-change="()=>{riverPagination.page=1;fetchRiverList()}" @current-change="fetchRiverList" />
        </div>
        <el-dialog v-model="riverDialogVisible" :title="riverEditMode?'编辑河流':'新增河流'" width="520px" :close-on-click-modal="false" @close="resetRiverForm">
          <el-form ref="riverFormRef" :model="riverForm" :rules="riverFormRules" label-width="110px">
            <el-form-item label="河流名称" prop="name">
              <el-input v-model="riverForm.name" placeholder="请输入" maxlength="100" :disabled="riverEditMode" />
            </el-form-item>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="长度(km)" prop="length">
                  <el-input-number v-model="riverForm.length" :min="0" :max="99999" :precision="2" class="w-full" controls-position="right" placeholder="选填" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="所属流域" prop="watershed">
                  <el-select v-model="riverForm.watershed" placeholder="选填" clearable class="w-full">
                    <el-option label="淮河流域" value="淮河流域" />
                    <el-option label="长江流域" value="长江流域" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="注入水库编号" prop="flows_into_reservoir_code">
              <el-select v-model="riverForm.flows_into_reservoir_code" placeholder="选填" clearable filterable class="w-full">
                <el-option v-for="item in neo4jReservoirOptions" :key="item.code" :label="`${item.name}(${item.code})`" :value="item.code" />
              </el-select>
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="riverDialogVisible=false">取消</el-button>
            <el-button type="primary" :loading="riverSubmitLoading" @click="handleRiverSubmit">{{ riverEditMode?'保 存':'确 定' }}</el-button>
          </template>
        </el-dialog>
      </el-tab-pane>

      <el-tab-pane label="污染源管理" name="pollution">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-3">
            <el-select v-model="psFilterType" placeholder="类型" clearable class="w-36" @change="fetchPollutionSourceList">
              <el-option label="养殖场" value="养殖场" /><el-option label="工业企业" value="工业企业" /><el-option label="农业面源" value="农业面源" /><el-option label="其他" value="其他" />
            </el-select>
            <el-select v-model="psFilterRiskLevel" placeholder="风险等级" clearable class="w-32" @change="fetchPollutionSourceList">
              <el-option label="高" value="高" /><el-option label="中" value="中" /><el-option label="低" value="低" />
            </el-select>
          </div>
          <el-button type="primary" @click="openPsDialog()"><el-icon><Plus /></el-icon>新增污染源</el-button>
        </div>
        <el-table v-loading="psLoading" :data="psList" border stripe class="w-full">
          <el-table-column prop="name" label="名称" min-width="140" />
          <el-table-column prop="type" label="类型" width="90" />
          <el-table-column label="经纬度" width="200">
            <template #default="{ row }">
              <div class="flex flex-col gap-0.5">
                <div class="flex items-center gap-2"><span class="text-xs text-gray-400 shrink-0">经度</span><span class="font-mono text-sm">{{ Number(row.longitude).toFixed(6) }}</span></div>
                <div class="flex items-center gap-2"><span class="text-xs text-gray-400 shrink-0">纬度</span><span class="font-mono text-sm">{{ Number(row.latitude).toFixed(6) }}</span></div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="risk_level" label="风险等级" width="90" align="center">
            <template #default="{ row }"><el-tag :type="riskTagType(row.risk_level)" size="small" effect="dark">{{ row.risk_level }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="violation_count" label="违规次数" width="90" align="center" />
          <el-table-column prop="discharges_into_river_name" label="排入河流" width="120">
            <template #default="{ row }">{{ row.discharges_into_river_name || '-' }}</template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click="openPsDialog(row)">编辑</el-button>
              <el-button type="danger" link size="small" @click="handleDeletePs(row)">删除</el-button>
            </template>
          </el-table-column>
          <template #empty><el-empty description="暂无污染源数据" /></template>
        </el-table>
        <div class="flex justify-end mt-4">
          <el-pagination v-model:current-page="psPagination.page" v-model:page-size="psPagination.page_size" :total="psPagination.total" :page-sizes="[10,20,50]" layout="total, sizes, prev, pager, next, jumper" background @size-change="()=>{psPagination.page=1;fetchPollutionSourceList()}" @current-change="fetchPollutionSourceList" />
        </div>
        <el-dialog v-model="psDialogVisible" :title="psEditMode?'编辑污染源':'新增污染源'" width="600px" :close-on-click-modal="false" @close="resetPsForm">
          <el-form ref="psFormRef" :model="psForm" :rules="psFormRules" label-width="110px">
            <el-form-item label="名称" prop="name">
              <el-input v-model="psForm.name" placeholder="请输入" maxlength="200" :disabled="psEditMode" />
            </el-form-item>
            <el-row :gutter="20">
              <el-col :span="12"><el-form-item label="类型" prop="type"><el-select v-model="psForm.type" placeholder="请选择" class="w-full"><el-option label="养殖场" value="养殖场" /><el-option label="工业企业" value="工业企业" /><el-option label="农业面源" value="农业面源" /><el-option label="其他" value="其他" /></el-select></el-form-item></el-col>
              <el-col :span="12"><el-form-item label="风险等级" prop="risk_level"><el-select v-model="psForm.risk_level" placeholder="请选择" class="w-full"><el-option label="高" value="高" /><el-option label="中" value="中" /><el-option label="低" value="低" /></el-select></el-form-item></el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12"><el-form-item label="经度" prop="longitude"><el-input-number v-model="psForm.longitude" :min="0" :max="180" :precision="6" :step="0.01" class="w-full" controls-position="right" /></el-form-item></el-col>
              <el-col :span="12"><el-form-item label="纬度" prop="latitude"><el-input-number v-model="psForm.latitude" :min="0" :max="90" :precision="6" :step="0.01" class="w-full" controls-position="right" /></el-form-item></el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12"><el-form-item label="违规次数" prop="violation_count"><el-input-number v-model="psForm.violation_count" :min="0" :max="99999" class="w-full" controls-position="right" /></el-form-item></el-col>
              <el-col :span="12"><el-form-item label="距水库(km)" prop="distance_km"><el-input-number v-model="psForm.distance_km" :min="0" :max="999" :precision="2" class="w-full" controls-position="right" placeholder="选填" /></el-form-item></el-col>
            </el-row>
            <el-form-item label="排入河流" prop="discharges_into_river_name">
              <el-select v-model="psForm.discharges_into_river_name" placeholder="选填" clearable filterable class="w-full">
                <el-option v-for="item in riverOptions" :key="item.name" :label="item.name" :value="item.name" />
              </el-select>
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="psDialogVisible=false">取消</el-button>
            <el-button type="primary" :loading="psSubmitLoading" @click="handlePsSubmit">{{ psEditMode?'保 存':'确 定' }}</el-button>
          </template>
        </el-dialog>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
/**
 * 图谱实体管理 Tab
 * 功能描述：水库/站点/指标/河流/污染源 五类图谱实体的CRUD管理，直接操作Neo4j
 * 依赖组件：无
 */
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getRiverList, createRiver, getRiverDetail, updateRiver, deleteRiver,
  getPollutionSourceList, createPollutionSource, getPollutionSourceDetail,
  updatePollutionSource, deletePollutionSource,
  getNeo4jReservoirList, createNeo4jReservoir, getNeo4jReservoirDetail,
  updateNeo4jReservoir, deleteNeo4jReservoir,
  getNeo4jStationList, createNeo4jStation, getNeo4jStationDetail,
  updateNeo4jStation, deleteNeo4jStation,
  getNeo4jIndicatorList, createNeo4jIndicator, getNeo4jIndicatorDetail,
  updateNeo4jIndicator, deleteNeo4jIndicator,
} from '@/api/graph_admin'

const activeTab = ref('reservoir')
const neo4jReservoirOptions = ref([])

const riskTagType = (level) => ({ 高: 'danger', 中: 'warning', 低: 'info' })[level] || 'info'

/* ========== 水库 ========== */
const reservoirFilterWatershed = ref(null)
const reservoirList = ref([])
const reservoirLoading = ref(false)
const reservoirPagination = reactive({ page: 1, page_size: 10, total: 0, total_pages: 0 })
const reservoirDialogVisible = ref(false)
const reservoirEditMode = ref(false)
const reservoirSubmitLoading = ref(false)
const reservoirFormRef = ref(null)
const editingReservoirCode = ref(null)
const reservoirForm = reactive({ code: '', name: '', location: '', longitude: '', latitude: '', capacity: '', water_grade: '', watershed: '' })
const reservoirFormRules = { code: [{ required: true, message: '请输入水库编号', trigger: 'blur' }], name: [{ required: true, message: '请输入水库名称', trigger: 'blur' }] }

const fetchReservoirList = async () => {
  reservoirLoading.value = true
  try {
    const params = { page: reservoirPagination.page, page_size: reservoirPagination.page_size, watershed: reservoirFilterWatershed.value ?? undefined }
    const res = await getNeo4jReservoirList(params)
    reservoirList.value = res.data.lists || []
    reservoirPagination.total = res.data.pagination.total
    reservoirPagination.total_pages = res.data.pagination.total_pages
  } catch (e) { ElMessage.error(e.message || '获取列表失败'); reservoirList.value = []
  } finally { reservoirLoading.value = false }
}

const fetchNeo4jReservoirOptions = async () => {
  try { const res = await getNeo4jReservoirList({ page: 1, page_size: 100 }); neo4jReservoirOptions.value = res.data.lists || [] } catch { /* 静默 */ }
}

const openReservoirDialog = async (row) => {
  if (row) {
    reservoirEditMode.value = true; editingReservoirCode.value = row.code; reservoirDialogVisible.value = true
    try { const res = await getNeo4jReservoirDetail(row.code); const d = res.data; Object.assign(reservoirForm, { code: d.code, name: d.name, location: d.location ?? '', longitude: d.longitude ?? '', latitude: d.latitude ?? '', capacity: d.capacity ?? '', water_grade: d.water_grade ?? '', watershed: d.watershed ?? '' }) }
    catch (e) { ElMessage.error(e.message || '获取详情失败'); reservoirDialogVisible.value = false }
  } else {
    reservoirEditMode.value = false; editingReservoirCode.value = null; reservoirDialogVisible.value = true
  }
}
const resetReservoirForm = () => { reservoirEditMode.value = false; editingReservoirCode.value = null; reservoirForm.code = ''; reservoirForm.name = ''; reservoirForm.location = ''; reservoirForm.longitude = ''; reservoirForm.latitude = ''; reservoirForm.capacity = ''; reservoirForm.water_grade = ''; reservoirForm.watershed = ''; reservoirFormRef.value?.clearValidate() }
const handleReservoirSubmit = async () => {
  if (!reservoirFormRef.value) return
  try { await reservoirFormRef.value.validate() } catch { return }
  reservoirSubmitLoading.value = true
  try {
    const p = { ...reservoirForm }
    Object.keys(p).forEach(k => { if (p[k] === '') p[k] = undefined })
    if (reservoirEditMode.value) { await updateNeo4jReservoir(editingReservoirCode.value, p); ElMessage.success('更新成功') }
    else { await createNeo4jReservoir(p); ElMessage.success('创建成功') }
    reservoirDialogVisible.value = false; await fetchReservoirList()
  } catch (e) { ElMessage.error(e.message || '操作失败')
  } finally { reservoirSubmitLoading.value = false }
}
const handleDeleteReservoir = async (row) => {
  try { await ElMessageBox.confirm(`确定删除水库「${row.name}」？`, '删除确认', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }) } catch { return }
  try { await deleteNeo4jReservoir(row.code); ElMessage.success('删除成功'); await fetchReservoirList() } catch (e) { ElMessage.error(e.message || '删除失败') }
}

/* ========== 站点 ========== */
const stationFilterType = ref(null)
const stationList = ref([])
const stationLoading = ref(false)
const stationPagination = reactive({ page: 1, page_size: 10, total: 0, total_pages: 0 })
const stationDialogVisible = ref(false)
const stationEditMode = ref(false)
const stationSubmitLoading = ref(false)
const stationFormRef = ref(null)
const editingStationCode = ref(null)
const stationForm = reactive({ code: '', name: '', type: '', longitude: '', latitude: '', sampling_point: '', reservoir_code: '' })
const stationFormRules = { code: [{ required: true, message: '请输入站点编号', trigger: 'blur' }], name: [{ required: true, message: '请输入站点名称', trigger: 'blur' }], type: [{ required: true, message: '请选择类型', trigger: 'change' }] }

const fetchStationList = async () => {
  stationLoading.value = true
  try {
    const params = { page: stationPagination.page, page_size: stationPagination.page_size, station_type: stationFilterType.value ?? undefined }
    const res = await getNeo4jStationList(params)
    stationList.value = res.data.lists || []
    stationPagination.total = res.data.pagination.total; stationPagination.total_pages = res.data.pagination.total_pages
  } catch (e) { ElMessage.error(e.message || '获取列表失败'); stationList.value = []
  } finally { stationLoading.value = false }
}
const openStationDialog = async (row) => {
  if (row) {
    stationEditMode.value = true; editingStationCode.value = row.code; stationDialogVisible.value = true
    try { const res = await getNeo4jStationDetail(row.code); const d = res.data; Object.assign(stationForm, { code: d.code, name: d.name, type: d.type ?? '', longitude: d.longitude ?? '', latitude: d.latitude ?? '', sampling_point: d.sampling_point ?? '', reservoir_code: d.reservoir_code ?? '' }) }
    catch (e) { ElMessage.error(e.message || '获取详情失败'); stationDialogVisible.value = false }
  } else { stationEditMode.value = false; editingStationCode.value = null; stationDialogVisible.value = true }
}
const resetStationForm = () => { stationEditMode.value = false; editingStationCode.value = null; stationForm.code = ''; stationForm.name = ''; stationForm.type = ''; stationForm.longitude = ''; stationForm.latitude = ''; stationForm.sampling_point = ''; stationForm.reservoir_code = ''; stationFormRef.value?.clearValidate() }
const handleStationSubmit = async () => {
  if (!stationFormRef.value) return
  try { await stationFormRef.value.validate() } catch { return }
  stationSubmitLoading.value = true
  try {
    const p = { ...stationForm }; Object.keys(p).forEach(k => { if (p[k] === '') p[k] = undefined })
    if (stationEditMode.value) { await updateNeo4jStation(editingStationCode.value, p); ElMessage.success('更新成功') }
    else { await createNeo4jStation(p); ElMessage.success('创建成功') }
    stationDialogVisible.value = false; await fetchStationList()
  } catch (e) { ElMessage.error(e.message || '操作失败')
  } finally { stationSubmitLoading.value = false }
}
const handleDeleteStation = async (row) => {
  try { await ElMessageBox.confirm(`确定删除站点「${row.name}」？`, '删除确认', { type: 'warning' }) } catch { return }
  try { await deleteNeo4jStation(row.code); ElMessage.success('删除成功'); await fetchStationList() } catch (e) { ElMessage.error(e.message || '删除失败') }
}

/* ========== 指标 ========== */
const indicatorFilterCategory = ref(null)
const indicatorList = ref([])
const indicatorLoading = ref(false)
const indicatorPagination = reactive({ page: 1, page_size: 10, total: 0, total_pages: 0 })
const indicatorDialogVisible = ref(false)
const indicatorEditMode = ref(false)
const indicatorSubmitLoading = ref(false)
const indicatorFormRef = ref(null)
const editingIndicatorCode = ref(null)
const indicatorForm = reactive({ code: '', name: '', unit: '', category: '' })
const indicatorFormRules = { code: [{ required: true, message: '请输入指标编码', trigger: 'blur' }], name: [{ required: true, message: '请输入指标名称', trigger: 'blur' }] }

const fetchIndicatorList = async () => {
  indicatorLoading.value = true
  try {
    const params = { page: indicatorPagination.page, page_size: indicatorPagination.page_size, category: indicatorFilterCategory.value ?? undefined }
    const res = await getNeo4jIndicatorList(params)
    indicatorList.value = res.data.lists || []
    indicatorPagination.total = res.data.pagination.total; indicatorPagination.total_pages = res.data.pagination.total_pages
  } catch (e) { ElMessage.error(e.message || '获取列表失败'); indicatorList.value = []
  } finally { indicatorLoading.value = false }
}
const openIndicatorDialog = async (row) => {
  if (row) {
    indicatorEditMode.value = true; editingIndicatorCode.value = row.code; indicatorDialogVisible.value = true
    try { const res = await getNeo4jIndicatorDetail(row.code); const d = res.data; Object.assign(indicatorForm, { code: d.code, name: d.name, unit: d.unit ?? '', category: d.category ?? '' }) }
    catch (e) { ElMessage.error(e.message || '获取详情失败'); indicatorDialogVisible.value = false }
  } else { indicatorEditMode.value = false; editingIndicatorCode.value = null; indicatorDialogVisible.value = true }
}
const resetIndicatorForm = () => { indicatorEditMode.value = false; editingIndicatorCode.value = null; indicatorForm.code = ''; indicatorForm.name = ''; indicatorForm.unit = ''; indicatorForm.category = ''; indicatorFormRef.value?.clearValidate() }
const handleIndicatorSubmit = async () => {
  if (!indicatorFormRef.value) return
  try { await indicatorFormRef.value.validate() } catch { return }
  indicatorSubmitLoading.value = true
  try {
    const p = { ...indicatorForm }; Object.keys(p).forEach(k => { if (p[k] === '') p[k] = undefined })
    if (indicatorEditMode.value) { await updateNeo4jIndicator(editingIndicatorCode.value, p); ElMessage.success('更新成功') }
    else { await createNeo4jIndicator(p); ElMessage.success('创建成功') }
    indicatorDialogVisible.value = false; await fetchIndicatorList()
  } catch (e) { ElMessage.error(e.message || '操作失败')
  } finally { indicatorSubmitLoading.value = false }
}
const handleDeleteIndicator = async (row) => {
  try { await ElMessageBox.confirm(`确定删除指标「${row.name}」？`, '删除确认', { type: 'warning' }) } catch { return }
  try { await deleteNeo4jIndicator(row.code); ElMessage.success('删除成功'); await fetchIndicatorList() } catch (e) { ElMessage.error(e.message || '删除失败') }
}

/* ========== 河流 ========== */
const riverFilterWatershed = ref(null)
const riverList = ref([])
const riverLoading = ref(false)
const riverPagination = reactive({ page: 1, page_size: 10, total: 0, total_pages: 0 })
const riverDialogVisible = ref(false)
const riverEditMode = ref(false)
const riverSubmitLoading = ref(false)
const riverFormRef = ref(null)
const editingRiverName = ref(null)
const riverForm = reactive({ name: '', length: null, watershed: null, flows_into_reservoir_code: null })
const riverFormRules = { name: [{ required: true, message: '请输入河流名称', trigger: 'blur' }] }

const fetchRiverList = async () => {
  riverLoading.value = true
  try {
    const params = { page: riverPagination.page, page_size: riverPagination.page_size, watershed: riverFilterWatershed.value ?? undefined }
    const res = await getRiverList(params)
    riverList.value = res.data.lists || []
    riverPagination.total = res.data.pagination.total; riverPagination.total_pages = res.data.pagination.total_pages
  } catch (e) { ElMessage.error(e.message || '获取列表失败'); riverList.value = []
  } finally { riverLoading.value = false }
}
const openRiverDialog = async (row) => {
  if (row) {
    riverEditMode.value = true; editingRiverName.value = row.name; riverDialogVisible.value = true
    try { const res = await getRiverDetail(row.name); const d = res.data; riverForm.name = d.name; riverForm.length = d.length ?? null; riverForm.watershed = d.watershed ?? null; riverForm.flows_into_reservoir_code = d.flows_into_reservoir_code ?? null }
    catch (e) { ElMessage.error(e.message || '获取详情失败'); riverDialogVisible.value = false }
  } else { riverEditMode.value = false; editingRiverName.value = null; riverDialogVisible.value = true }
}
const resetRiverForm = () => { riverEditMode.value = false; editingRiverName.value = null; riverForm.name = ''; riverForm.length = null; riverForm.watershed = null; riverForm.flows_into_reservoir_code = null; riverFormRef.value?.clearValidate() }
const handleRiverSubmit = async () => {
  if (!riverFormRef.value) return
  try { await riverFormRef.value.validate() } catch { return }
  riverSubmitLoading.value = true
  try {
    const p = { name: riverForm.name, length: riverForm.length ?? undefined, watershed: riverForm.watershed ?? undefined, flows_into_reservoir_code: riverForm.flows_into_reservoir_code ?? undefined }
    if (riverEditMode.value) { await updateRiver(editingRiverName.value, p); ElMessage.success('更新成功') }
    else { await createRiver(p); ElMessage.success('创建成功') }
    riverDialogVisible.value = false; await fetchRiverList()
  } catch (e) { ElMessage.error(e.message || '操作失败')
  } finally { riverSubmitLoading.value = false }
}
const handleDeleteRiver = async (row) => {
  try { await ElMessageBox.confirm(`确定删除河流「${row.name}」？`, '删除确认', { type: 'warning' }) } catch { return }
  try { await deleteRiver(row.name); ElMessage.success('删除成功'); await fetchRiverList() } catch (e) { ElMessage.error(e.message || '删除失败') }
}

/* ========== 污染源 ========== */
const psFilterType = ref(null)
const psFilterRiskLevel = ref(null)
const psList = ref([])
const psLoading = ref(false)
const psPagination = reactive({ page: 1, page_size: 10, total: 0, total_pages: 0 })
const psDialogVisible = ref(false)
const psEditMode = ref(false)
const psSubmitLoading = ref(false)
const psFormRef = ref(null)
const editingPsName = ref(null)
const riverOptions = ref([])
const psForm = reactive({ name: '', type: '', longitude: null, latitude: null, risk_level: '', violation_count: 0, discharges_into_river_name: null, distance_km: null })
const psFormRules = { name: [{ required: true, message: '请输入名称', trigger: 'blur' }], type: [{ required: true, message: '请选择类型', trigger: 'change' }], longitude: [{ required: true, message: '请输入经度', trigger: 'blur' }], latitude: [{ required: true, message: '请输入纬度', trigger: 'blur' }], risk_level: [{ required: true, message: '请选择风险等级', trigger: 'change' }] }

const fetchPollutionSourceList = async () => {
  psLoading.value = true
  try {
    const params = { page: psPagination.page, page_size: psPagination.page_size, source_type: psFilterType.value ?? undefined, risk_level: psFilterRiskLevel.value ?? undefined }
    const res = await getPollutionSourceList(params)
    psList.value = res.data.lists || []; psPagination.total = res.data.pagination.total; psPagination.total_pages = res.data.pagination.total_pages
  } catch (e) { ElMessage.error(e.message || '获取列表失败'); psList.value = []
  } finally { psLoading.value = false }
}
const fetchRiverOptions = async () => {
  try { const res = await getRiverList({ page: 1, page_size: 100 }); riverOptions.value = res.data.lists || [] } catch { /* 静默 */ }
}
const openPsDialog = async (row) => {
  if (row) {
    psEditMode.value = true; editingPsName.value = row.name; psDialogVisible.value = true
    try { const res = await getPollutionSourceDetail(row.name); const d = res.data; Object.assign(psForm, { name: d.name, type: d.type, longitude: d.longitude, latitude: d.latitude, risk_level: d.risk_level, violation_count: d.violation_count, discharges_into_river_name: d.discharges_into_river_name ?? null, distance_km: d.distance_km ?? null }) }
    catch (e) { ElMessage.error(e.message || '获取详情失败'); psDialogVisible.value = false }
  } else { psEditMode.value = false; editingPsName.value = null; psDialogVisible.value = true }
}
const resetPsForm = () => { psEditMode.value = false; editingPsName.value = null; psForm.name = ''; psForm.type = ''; psForm.longitude = null; psForm.latitude = null; psForm.risk_level = ''; psForm.violation_count = 0; psForm.discharges_into_river_name = null; psForm.distance_km = null; psFormRef.value?.clearValidate() }
const handlePsSubmit = async () => {
  if (!psFormRef.value) return
  try { await psFormRef.value.validate() } catch { return }
  psSubmitLoading.value = true
  try {
    const p = { name: psForm.name, type: psForm.type, longitude: psForm.longitude, latitude: psForm.latitude, risk_level: psForm.risk_level, violation_count: psForm.violation_count, discharges_into_river_name: psForm.discharges_into_river_name ?? undefined, distance_km: psForm.distance_km ?? undefined }
    if (psEditMode.value) { await updatePollutionSource(editingPsName.value, p); ElMessage.success('更新成功') }
    else { await createPollutionSource(p); ElMessage.success('创建成功') }
    psDialogVisible.value = false; await fetchPollutionSourceList()
  } catch (e) { ElMessage.error(e.message || '操作失败')
  } finally { psSubmitLoading.value = false }
}
const handleDeletePs = async (row) => {
  try { await ElMessageBox.confirm(`确定删除污染源「${row.name}」？`, '删除确认', { type: 'warning' }) } catch { return }
  try { await deletePollutionSource(row.name); ElMessage.success('删除成功'); await fetchPollutionSourceList() } catch (e) { ElMessage.error(e.message || '删除失败') }
}

onMounted(() => {
  fetchNeo4jReservoirOptions()
  fetchRiverOptions()
  fetchReservoirList()
  fetchStationList()
  fetchIndicatorList()
  fetchRiverList()
  fetchPollutionSourceList()
})
</script>
