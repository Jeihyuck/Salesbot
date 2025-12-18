<template>
  <v-col style="height: calc(100vh - 90px); overflow-y: auto;">

    <!-- Existing privacy queue sections... -->
    <v-row class="pa-5">
      <v-btn @click="checkPrivacyQueue()"> Get Queued Privacy Tickets</v-btn>
    </v-row>

    <v-row class="pa-2">
      <v-col>
        <v-data-table
          :headers="headers1"
          :items="privacyQueue"
          :loading="loading1"
          loading-text="Loading..."
          class="elevation-1"
        >
          
        <template #body.prepend>
          <tr>
            <td v-for="col in headers1" :key="col.value">
              {{ col.text }}
            </td>
          </tr>
        </template>

        <template #no-data>
          No ticket found.
        </template>
        </v-data-table>
      </v-col>
    </v-row>

    <v-row class="pa-5" v-if="privacyQueue && privacyQueue.length > 0">
      <v-btn @click="processPrivacyQueue()"> Process Privacy Tickets</v-btn>
    </v-row>

    <v-row class="pa-2" v-if="privacyQueue && privacyQueue.length > 0">
      <v-col>
        <v-data-table
          :headers="headers2"
          :items="privacyQueueResult"
          :loading="loading2"
          loading-text="Loading..."
          class="elevation-1"
        >

          <template #body.prepend>
            <tr>
              <td v-for="col in headers2" :key="col.value">
                {{ col.text }}
              </td>
            </tr>
          </template>
          
          <template #no-data>
            No ticket proccessed.
          </template>
        </v-data-table>
      </v-col>
    </v-row>

    <!-- Updated Chat Logs Search Section -->
    <v-row class="pa-5">
      <v-col>
        <v-card>
          <v-card-title>Chat Logs Search</v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="searchCriteria.guid"
                  label="GUID"
                  placeholder="Enter GUID"
                  clearable
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="searchCriteria.userid"
                  label="User ID"
                  placeholder="Enter User ID"
                  clearable
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model="searchCriteria.said"
                  label="SA ID"
                  placeholder="Enter SA ID"
                  clearable
                ></v-text-field>
              </v-col>
            </v-row>
            <v-row>
              <v-col>
                <v-btn 
                  @click="getChatLogs()" 
                  color="primary"
                  :loading="loadingChatLogs"
                  :disabled="!hasSearchCriteria"
                >
                  Get Chat Logs
                </v-btn>
                <v-btn 
                  @click="clearChatLogs()" 
                  color="secondary"
                  class="ml-2"
                  :disabled="chatLogs.length === 0"
                >
                  Clear Chat Logs
                </v-btn>
                <!-- Execute Task Button -->
                <v-btn 
                  @click="showExecuteTaskDialog = true" 
                  color="info"
                  class="ml-2"
                  :disabled="selectedChatLogs.length === 0"
                >
                  Execute Task ({{ selectedChatLogs.length }})
                </v-btn>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Updated Chat Logs Results Table with Checkboxes -->
    <v-row class="pa-2" v-if="chatLogs.length > 0 || loadingChatLogs">
      <v-col>
        <v-card>
          <v-card-title>
            Chat Logs Results
            <v-spacer></v-spacer>
            <span class="text-subtitle-1">
              Total: {{ chatLogs.length }} records | Selected: {{ selectedChatLogs.length }}
            </span>
          </v-card-title>
          <v-card-text>
            <v-data-table
            :headers="chatLogsHeaders"
            :items="chatLogs"
            :loading="loadingChatLogs"
            loading-text="Loading chat logs..."
            class="elevation-1"
            :items-per-page="10"
            :search="chatLogsSearch"
            item-key="messageid"
            >

              <template v-slot:top>
                <v-row class="ma-0 pa-2">
                  <v-col cols="12" md="4" class="d-flex align-center">
                    <v-btn
                      @click="selectAll"
                      color="primary"
                      small
                      outlined
                      class="mr-2"
                    >
                      Select All
                    </v-btn>
                    <v-btn
                      @click="selectNone"
                      color="secondary"
                      small
                      outlined
                    >
                      Select None
                    </v-btn>
                  </v-col>
                </v-row>
              </template>

              <!-- Make entire row clickable using v-slot:item -->
              <template v-slot:item="{ item }">
              <tr 
                :class="{ 
                  'selected-row': selectedChatLogs.some(selected => selected.messageid === item.messageid),
                  'manual-selected': selectedChatLogs.some(selected => selected.messageid === item.messageid)
                }"
                @click="handleRowClick(item)"
                style="cursor: pointer;"
              >
                <!-- Message ID Column with truncation -->
                <td class="truncate-cell">
                  <v-tooltip bottom max-width="400px">
                    <template v-slot:activator="{ on, attrs }">
                      <div 
                        class="truncated-text copyable-cell" 
                        v-bind="attrs"
                        v-on="on"
                        @click.stop="copyToClipboard(item.messageid, 'Message ID')"
                      >
                        {{ truncateText(item.messageid) }}
                        <v-icon x-small class="copy-icon ml-1">mdi-content-copy</v-icon>
                      </div>
                    </template>
                    <div>
                      <strong>Full Message ID:</strong><br>
                      {{ item.messageid }}<br>
                      <em>Click to copy full text</em>
                    </div>
                  </v-tooltip>
                </td>

                <!-- GUID Column with truncation -->
                <td class="truncate-cell">
                  <v-tooltip bottom max-width="400px">
                    <template v-slot:activator="{ on, attrs }">
                      <div 
                        class="truncated-text copyable-cell" 
                        v-bind="attrs"
                        v-on="on"
                        @click.stop="copyToClipboard(item.guid, 'GUID')"
                      >
                        {{ truncateText(item.guid, 20) }}
                        <v-icon x-small class="copy-icon ml-1">mdi-content-copy</v-icon>
                      </div>
                    </template>
                    <div>
                      <strong>Full GUID:</strong><br>
                      {{ item.guid }}<br>
                      <em>Click to copy full text</em>
                    </div>
                  </v-tooltip>
                </td>

                <!-- SA ID Column with truncation -->
                <td class="truncate-cell">
                  <v-tooltip bottom max-width="300px">
                    <template v-slot:activator="{ on, attrs }">
                      <div 
                        class="truncated-text copyable-cell" 
                        v-bind="attrs"
                        v-on="on"
                        @click.stop="copyToClipboard(item.said, 'SA ID')"
                      >
                        {{ truncateText(item.said, 15) }}
                        <v-icon x-small class="copy-icon ml-1">mdi-content-copy</v-icon>
                      </div>
                    </template>
                    <div>
                      <strong>Full SA ID:</strong><br>
                      {{ item.said }}<br>
                      <em>Click to copy full text</em>
                    </div>
                  </v-tooltip>
                </td>

                <!-- User ID Column with truncation -->
                <td class="truncate-cell">
                  <v-tooltip bottom max-width="300px">
                    <template v-slot:activator="{ on, attrs }">
                      <div 
                        class="truncated-text copyable-cell" 
                        v-bind="attrs"
                        v-on="on"
                        @click.stop="copyToClipboard(item.userid, 'User ID')"
                      >
                        {{ truncateText(item.userid) }}
                        <v-icon x-small class="copy-icon ml-1">mdi-content-copy</v-icon>
                      </div>
                    </template>
                    <div>
                      <strong>Full User ID:</strong><br>
                      {{ item.userid }}<br>
                      <em>Click to copy full text</em>
                    </div>
                  </v-tooltip>
                </td>

                <!-- Created Date Column with truncation -->
                <td class="truncate-cell">
                  <v-tooltip bottom max-width="300px">
                    <template v-slot:activator="{ on, attrs }">
                      <div 
                        class="truncated-text copyable-cell" 
                        v-bind="attrs"
                        v-on="on"
                      >
                        {{ truncateText(formatDateTime(item.created)) }}
                      </div>
                    </template>
                    <div>
                      <strong>Full Created Date:</strong><br>
                      {{ formatDateTime(item.created) }}<br>
                      <em>Click to copy full text</em>
                    </div>
                  </v-tooltip>
                </td>

                <!-- Updated Date Column with truncation -->
                <td class="truncate-cell">
                  <v-tooltip bottom max-width="300px">
                    <template v-slot:activator="{ on, attrs }">
                      <div 
                        class="truncated-text copyable-cell" 
                        v-bind="attrs"
                        v-on="on"
                      >
                        {{ truncateText(formatDateTime(item.updated)) }}
                      </div>
                    </template>
                    <div>
                      <strong>Full Updated Date:</strong><br>
                      {{ formatDateTime(item.updated) }}<br>
                      <em>Click to copy full text</em>
                    </div>
                  </v-tooltip>
                </td>

                <!-- Status Column -->
                <td class="text-center">
                  <v-chip
                    :color="getStatusColor(item.status)"
                    small
                    class="copyable-chip"
                  >
                    {{ item.status }}
                  </v-chip>
                </td>
              </tr>
            </template>

              <template v-slot:no-data>
                <div class="text-center pa-4">
                  <v-icon size="48" color="grey">mdi-database-search</v-icon>
                  <p class="mt-2">No chat logs found</p>
                </div>
              </template>

              <template #body.prepend>
                <tr>
                  <td v-for="col in chatLogsHeaders" :key="col.value">
                    {{ col.text }}
                  </td>
                </tr>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Sample Task Dialog/Popup -->
    <v-dialog v-model="showExecuteTaskDialog" max-width="80%" max-height="80%">
      <v-card>
        <v-card-title class="d-flex justify-space-between align-center">
          <span>Execute Task - Selected Chat Logs</span>
          <v-btn icon @click="showExecuteTaskDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        
        <v-card-text style="height: 500px; overflow-y: auto;">
          <!-- Task Options -->
          <v-row class="mb-4">
            <v-col cols="12">
              <v-card outlined>
                <v-card-title class="text-h6">Available Tasks</v-card-title>
                <v-card-text>
                  <v-row>
                    <v-col cols="12" md="6">
                      <v-btn 
                        @click="executeTask('hide')"
                        color="warning"
                        block
                        :loading="taskLoading"
                      >
                        <v-icon left>mdi-eye-off</v-icon>
                        Hide Selected Messages
                      </v-btn>
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-btn 
                        @click="executeTask('unhide')"
                        color="success"
                        block
                        :loading="taskLoading"
                      >
                        <v-icon left>mdi-eye</v-icon>
                        Unhide Selected Messages
                      </v-btn>
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-btn 
                        @click="executeTask('delete')"
                        color="error"
                        block
                        :loading="taskLoading"
                      >
                        <v-icon left>mdi-delete</v-icon>
                        Delete Selected Messages
                      </v-btn>
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-btn 
                        @click="executeTask('export')"
                        color="success"
                        block
                        :loading="taskLoading"
                      >
                        <v-icon left>mdi-download</v-icon>
                        Export Selected Messages
                      </v-btn>
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>

          <!-- Selected Items Preview -->
          <v-row>
            <v-col cols="12">
              <v-card outlined>
                <v-card-title class="text-h6">
                  Selected Items ({{ selectedChatLogs.length }})
                </v-card-title>
                <v-card-text>
                  <v-simple-table dense class="aligned-table">
                    <template v-slot:default>
                      <thead>
                        <tr>
                          <th class="text-left table-header" style="width: 300px;">Message ID</th>
                          <th class="text-left table-header" style="width: 150px;">GUID</th>
                          <th class="text-center table-header" style="width: 100px;">Status</th>
                          <th class="text-left table-header" style="width: 180px;">Created</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="item in selectedChatLogs" :key="item.messageid" class="table-row">
                          <td class="text-left table-cell" style="width: 300px;">
                            <div class="text-truncate" style="max-width: 280px;">
                              {{ item.messageid }}
                            </div>
                          </td>
                          <td class="text-left table-cell" style="width: 150px;">
                            <div class="text-truncate" style="max-width: 130px;">
                              {{ item.guid }}
                            </div>
                          </td>
                          <td class="text-center table-cell" style="width: 100px;">
                            <v-chip 
                              :color="getStatusColor(item.status)" 
                              x-small
                              class="status-chip"
                            >
                              {{ item.status }}
                            </v-chip>
                          </td>
                          <td class="text-left table-cell" style="width: 180px;">
                            <div class="text-truncate" style="max-width: 160px;">
                              {{ formatDateTime(item.created) }}
                            </div>
                          </td>
                        </tr>
                      </tbody>
                    </template>
                  </v-simple-table>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>

          <!-- Task Results -->
          <v-row v-if="taskResult" class="mt-4">
            <v-col cols="12">
              <v-card outlined>
                <v-card-title class="text-h6">Task Results</v-card-title>
                <v-card-text>
                  <pre class="task-result">{{ taskResult }}</pre>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="clearSelection">Clear Selection</v-btn>
          <v-btn @click="showExecuteTaskDialog = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

  </v-col>
</template>

<script setup>
import { ref, computed } from 'vue'
import { rubiconAdmin } from '@/_services'

const privacyCheckResult = ref('-- Start --')
const privacyQueue = ref([])
const privacyQueueResult = ref([])
const loading1 = ref(false)
const loading2 = ref(false)

const chatLogs = ref([])
const loadingChatLogs = ref(false)
const chatLogsSearch = ref('')
const searchCriteria = ref({
  guid: '',
  userid: '',
  said: ''
})

// New reactive variables for execute task functionality
const selectedChatLogs = ref([])
const showExecuteTaskDialog = ref(false)
const taskLoading = ref(false)
const taskResult = ref('')

// predefined columns for the table
const headers1 = [
  { text: 'issue_date', value: 'issue_date' },
  { text: 'country_code', value: 'country_code' },
  { text: 'gk_id', value: 'gk_id' },
  { text: 'id_type_guid', value: 'id_type_guid' },
  { text: 'event_type', value: 'event_type' },
  { text: 'event_sub_type', value: 'event_sub_type' },
  { text: 'target_service_cd', value: 'target_service_cd' },
  { text: 'source_service_cd', value: 'source_service_cd' },
  { text: 'channel_type_code', value: 'channel_type_code' }
]

const headers2 = [
  { text: 'gk id', value: 'gk_id' },
  { text: 'status code', value: 'status_code' },
  { text: 'event type', value: 'event_type' },
  { text: 'response', value: 'response' },
  { text: 'log count', value: 'log_count' },
  { text: 'upload result', value: 'upload_result' },
  { text: 'upload url', value: 'upload_url' }
]

const chatLogsHeaders = [
  { 
    text: 'Message ID',     // This is the column name that will display
    value: 'messageid',     // This maps to your data property
    sortable: true,
    width: '200px',
    align: 'start'
  },
  { 
    text: 'GUID', 
    value: 'guid',
    sortable: true,
    width: '150px',
    align: 'start'
  },
  { 
    text: 'SA ID', 
    value: 'said',
    sortable: true,
    width: '120px',
    align: 'start'
  },
  { 
    text: 'User ID', 
    value: 'userid',
    sortable: true,
    width: '120px',
    align: 'start'
  },
  { 
    text: 'Created Date', 
    value: 'created',
    sortable: true,
    width: '180px',
    align: 'start'
  },
  { 
    text: 'Updated Date', 
    value: 'updated',
    sortable: true,
    width: '180px',
    align: 'start'
  },
  { 
    text: 'Status', 
    value: 'status',
    sortable: true,
    width: '100px',
    align: 'center'
  }
]

const hasSearchCriteria = computed(() => {
  return !!(searchCriteria.value.guid || 
           searchCriteria.value.userid || 
           searchCriteria.value.said)
})

// Add placeholder for addLogEntry function if it doesn't exist
function addLogEntry(message) {
  console.log(`[LOG]: ${message}`)
}

// Enhanced selection functions
function selectAll() {
  selectedChatLogs.value = [...chatLogs.value]
  addLogEntry(`Selected all ${chatLogs.value.length} chat logs`)
}

function selectNone() {
  selectedChatLogs.value = []
  addLogEntry('Cleared all selections')
}
function truncateText(text, maxLength = 40) {
  if (!text) return 'N/A'
  
  const textStr = String(text)
  
  if (textStr.length <= maxLength) {
    return textStr
  }
  
  return textStr.substring(0, maxLength) + '...'
}
function handleRowClick(item, select, isSelected) {
  console.log('Row clicked - item:', item)
  console.log('Row clicked - isSelected:', isSelected)
  
  if (!item || !item.messageid) {
    console.error('Invalid item received in handleRowClick:', item)
    addLogEntry('Error: Invalid item for row selection')
    return
  }

  console.log('Toggling selection for item:', item.messageid)
  
  // Check if message ID is already in selectedChatLogs
  const existingIndex = selectedChatLogs.value.findIndex(selected => selected.messageid === item.messageid)
  
  if (existingIndex > -1) {
    // Message ID is in selectedChatLogs, remove it
    selectedChatLogs.value.splice(existingIndex, 1)
    addLogEntry(`Deselected chat log: ${item.messageid}`)
    console.log('Removed from selection:', item.messageid)
  } else {
    // Message ID is not in selectedChatLogs, add it
    selectedChatLogs.value.push(item)
    addLogEntry(`Selected chat log: ${item.messageid}`)
    console.log('Added to selection:', item.messageid)
  }
  
  console.log('Current selections:', selectedChatLogs.value.map(i => i.messageid))
  console.log('Total selected:', selectedChatLogs.value.length)
}

function copyToClipboard(text) {
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(() => {
      addLogEntry(`Copied to clipboard: ${text}`)
      // You could add a toast notification here
    }).catch(err => {
      console.error('Failed to copy to clipboard:', err)
    })
  } else {
    // Fallback for older browsers
    const textArea = document.createElement('textarea')
    textArea.value = text
    document.body.appendChild(textArea)
    textArea.focus()
    textArea.select()
    try {
      document.execCommand('copy')
      addLogEntry(`Copied to clipboard: ${text}`)
    } catch (err) {
      console.error('Failed to copy to clipboard:', err)
    }
    document.body.removeChild(textArea)
  }
}

async function checkPrivacyQueue() {
  console.log('Checking Privacy Queue...')
  loading1.value = true
  
  try {
    const query = {}
    const response = await rubiconAdmin.privacy.function('getTicketGatekeeper', query)
    console.log('Privacy Queue Check:', response)
    privacyQueue.value = response.data || []
    addLogEntry(`Retrieved ${privacyQueue.value.length} privacy tickets from queue`)
  } catch (error) {
    console.error('Error checking privacy queue:', error)
    addLogEntry(`Error checking privacy queue: ${error.message}`)
    privacyQueue.value = []
  } finally {
    loading1.value = false
  }
}

async function processPrivacyQueue() {
  console.log('Processing Privacy Queue...')

  loading2.value = true
  addLogEntry(`Starting to process ${privacyQueue.value.length} privacy tickets...`)
  
  try {
    // Extract ticket IDs or relevant data from the checked queue
    const ticketsToProcess = privacyQueue.value

    console.log('Tickets to process:', ticketsToProcess)

    const { data } = await rubiconAdmin.privacy.function(
      'processTicketGatekeeper',
      {
        tickets: ticketsToProcess
      }
    )
    
    privacyQueueResult.value = data || []
    addLogEntry(`Successfully processed ${data?.length || 0} privacy tickets`)
    
    // Optionally refresh the queue after processing
    await checkPrivacyQueue()
    
  } catch (err) {
    console.error('Error processing privacy queue:', err)
    addLogEntry(`Error processing privacy queue: ${err.message}`)
    alert('Failed to process privacy tickets. Please check the console for details.')
  } finally {
    loading2.value = false
  }
}

async function getChatLogs() {
  if (!hasSearchCriteria.value) {
    alert('Please enter at least one search criteria (GUID, User ID, or SA ID)')
    return
  }

  loadingChatLogs.value = true
  addLogEntry('Starting chat logs retrieval...')

  try {
    // Prepare the query object with non-empty values
    const query = {}
    if (searchCriteria.value.guid) {
      query.guid = searchCriteria.value.guid.trim()
    }
    if (searchCriteria.value.userid) {
      query.userid = searchCriteria.value.userid.trim()
    }
    if (searchCriteria.value.said) {
      query.said = searchCriteria.value.said.trim()
    }

    console.log('Fetching chat logs with criteria:', query)
    addLogEntry(`Searching for chat logs with: ${JSON.stringify(query)}`)

    const { data } = await rubiconAdmin.privacy.function('getLogsByIdsGatekeeper', query)
    
    console.log('Chat logs response:', data)
    chatLogs.value = data || []
    
    addLogEntry(`Retrieved ${chatLogs.value.length} chat log records`)
    
    if (chatLogs.value.length === 0) {
      addLogEntry('No chat logs found for the given criteria')
    }

  } catch (error) {
    console.error('Error fetching chat logs:', error)
    addLogEntry('Failed to retrieve chat logs: ' + error.message)
    chatLogs.value = []
    
    // Show user-friendly error message
    alert('Failed to retrieve chat logs. Please check the console for details.')
  } finally {
    loadingChatLogs.value = false
    addLogEntry('Chat logs retrieval completed')
  }
}

// Function to clear chat logs
function clearChatLogs() {
  chatLogs.value = []
  selectedChatLogs.value = []
  searchCriteria.value = {
    guid: '',
    userid: '',
    said: ''
  }
  chatLogsSearch.value = ''
  addLogEntry('Chat logs cleared')
}

// New function to clear selection
function clearSelection() {
  selectedChatLogs.value = []
  addLogEntry('Selection cleared')
}

function downloadJsonFile(data, filename) {
  try {
    // Convert data to JSON string with proper formatting
    const jsonString = JSON.stringify(data, null, 2)
    
    // Create a Blob with the JSON data
    const blob = new Blob([jsonString], { type: 'application/json' })
    
    // Create a temporary URL for the blob
    const url = URL.createObjectURL(blob)
    
    // Create a temporary anchor element for download
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    
    // Append to body, click, and remove
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    // Clean up the URL object
    URL.revokeObjectURL(url)
    
    addLogEntry(`File downloaded: ${filename}`)
  } catch (error) {
    console.error('Error downloading file:', error)
    addLogEntry(`Error downloading file: ${error.message}`)
  }
}

// New function to execute sample tasks
async function executeTask(taskType) {
  if (selectedChatLogs.value.length === 0) {
    alert('Please select at least one chat log item')
    return
  }

  taskLoading.value = true
  taskResult.value = ''
  addLogEntry(`Starting ${taskType} task for ${selectedChatLogs.value.length} items...`)

  try {
    const messageIds = selectedChatLogs.value.map(item => item.messageid)
    
    switch (taskType) {
      case 'hide':
        // Call API to hide messages
        const hideResult = await rubiconAdmin.privacy.function('hideMessages', {
          message_ids: messageIds
        })
        taskResult.value = `Hide Task Completed:\n${JSON.stringify(hideResult.data, null, 2)}`
        addLogEntry(`Hide task completed for ${messageIds.length} messages`)
        break

      case 'unhide':
        // Call API to unhide messages
        const unhideResult = await rubiconAdmin.privacy.function('unhideMessages', {
          message_ids: messageIds
        })
        taskResult.value = `Unhide Task Completed:\n${JSON.stringify(unhideResult.data, null, 2)}`
        addLogEntry(`Unhide task completed for ${messageIds.length} messages`)
        break

      case 'delete':
        // Call API to delete messages
        const deleteResult = await rubiconAdmin.privacy.function('deleteMessages', {
          message_ids: messageIds
        })
        taskResult.value = `Delete Task Completed:\n${JSON.stringify(deleteResult.data, null, 2)}`
        addLogEntry(`Delete task completed for ${messageIds.length} messages`)
        break

      case 'export':
        // Call API to export messages
        const exportResult = await rubiconAdmin.privacy.function('exportMessages', {
          message_ids: messageIds,
          format: 'csv'
        })
        
        // Create filename with timestamp
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
        const filename = `chat_logs_export_${timestamp}.json`
        
        // Download the response as JSON file
        downloadJsonFile(exportResult.data, filename)
        
        // Update task result with download info
        taskResult.value = `Export Task Completed:\nFile downloaded: ${filename}\nExported ${messageIds.length} messages\n\nResponse preview:\n${JSON.stringify(exportResult.data, null, 2).substring(0, 500)}...`
        addLogEntry(`Export task completed for ${messageIds.length} messages - File downloaded: ${filename}`)
        break

      default:
        taskResult.value = `Unknown task type: ${taskType}`
    }

    // Refresh chat logs after task completion
    await getChatLogs()

  } catch (error) {
    console.error('Error executing sample task:', error)
    taskResult.value = `Error executing ${taskType} task:\n${error.message}`
    addLogEntry(`Failed to execute ${taskType} task: ${error.message}`)
  } finally {
    taskLoading.value = false
  }
}

// Utility function to format datetime
function formatDateTime(dateString) {
  if (!dateString) return 'N/A'
  
  try {
    const date = new Date(dateString)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    })
  } catch (error) {
    return dateString
  }
}

// Function to get status color for chips
function getStatusColor(status) {
  if (!status) return 'grey'
  
  switch (status.toLowerCase()) {
    case 'active':
    case 'success':
    case 'completed':
      return 'green'
    case 'inactive':
    case 'disabled':
      return 'red'
    case 'pending':
    case 'processing':
      return 'orange'
    case 'hidden':
      return 'grey'
    default:
      return 'blue'
  }
}

</script>


<style scoped>
.text-truncate {
  display: inline-block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-result {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  background-color: #333;
  color: #333;
  padding: 16px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 300px;
  overflow-y: auto;
}

/* Enhanced table styling */
.v-data-table >>> thead th {
  font-weight: 700 !important;
  background-color: #333 !important; /* Dark background for better readability */
  color: #f8f9fa !important; /* Light text for better contrast */
  border-bottom: 2px solid #dee2e6 !important;
  font-size: 14px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.5px !important;
  padding: 16px 8px !important;
}

.v-data-table >>> td {
  padding: 8px 16px !important;
  vertical-align: middle !important;
  border-bottom: 1px solid #e0e0e0 !important;
}

/* Row selection styles - Transparent Pink for manually selected rows */
.manual-selected,
.selected-row {
  background-color: rgba(233, 213, 30, 0.2) !important; /* Transparent pink */
  border-left: 4px solid #e91e63 !important; /* Pink left border */
}

.manual-selected:hover,
.selected-row:hover {
  background-color: rgba(233, 223, 30, 0.3) !important;
}

/* Regular hover effect for non-selected rows */
.v-data-table >>> tbody tr:hover:not(.manual-selected):not(.selected-row) {
  background-color: rgba(61, 230, 61, 0.4) !important;
}

/* Override Vuetify's default selection styling if it conflicts */
.v-data-table >>> tr.v-data-table__selected {
  background-color: rgba(233, 223, 30, 0.2) !important;
  border-left: 4px solid #e91e63 !important;
}

.message-id-cell:hover,
.guid-cell:hover {
  background-color: rgba(61, 230, 61, 0.4) !important;
  text-decoration: underline;
}

/* Checkbox styling */
.v-simple-checkbox {
  transform: scale(1.1);
}

/* Selection counter styling */
.text-subtitle-1 {
  font-weight: 500;
  color: #1976d2;
}

/* Ensure proper column alignment */
.v-data-table >>> thead th .v-data-table-header {
  display: flex !important;
  align-items: center !important;
  justify-content: space-between !important;
  white-space: nowrap !important;
}

/* Ensure first column (checkbox) has proper spacing */
.v-data-table >>> thead th:first-child {
  width: 60px !important;
  min-width: 60px !important;
  padding-left: 16px !important;
  padding-right: 8px !important;
}

/* Clickable row styling */
.v-data-table >>> tbody tr {
  cursor: pointer !important;
  transition: background-color 0.2s ease !important;
}
</style>