import { serviceAlpha } from '@/_services/index'

const assistantProductAPI = 'api/rubicon_admin/assistant_product/'
const assistantProduct = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'create_assistant_product',
      read: 'read_assistant_product',
      update: 'update_assistant_product',
      delete: 'delete_assistant_product',
      listCategory: 'list_category',
    }
    return serviceAlpha.stdPostFunction(
      assistantProductAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}

const assistantRefInfoAPI = 'api/rubicon_admin/assistant_ref_info/'
const assistantRefInfo = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'create_assistant_ref_info',
      read: 'read_assistant_ref_info',
      update: 'update_assistant_ref_info',
      delete: 'delete_assistant_ref_info',
      listCategory: 'list_category',
    }
    return serviceAlpha.stdPostFunction(
      assistantRefInfoAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}




const predefinedAPI = 'api/rubicon_admin/predefined/'
const predefined = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'create_predefined',
      read: 'read_predefined',
      update: 'update_predefined',
      delete: 'delete_predefined'
    }
    return serviceAlpha.stdPostFunction(
      predefinedAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}

const predefinedRAGAPI = 'api/rubicon_admin/predefined_rag/'
const predefinedRAG = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'create_predefined_rag',
      read: 'read_predefined_rag',
      update: 'update_predefined_rag',
      delete: 'delete_predefined_rag'
    }
    return serviceAlpha.stdPostFunction(
      predefinedRAGAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}


const managedResponseAPI = 'api/rubicon_admin/managed_response/'
const managedResponse = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'create_managed_response',
      read: 'read_managed_response',
      update: 'update_managed_response',
      delete: 'delete_managed_response',
    }
    return serviceAlpha.stdPostFunction(
      managedResponseAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}


const intelligenceAPI = 'api/rubicon_admin/intelligence/'
const intelligence = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'create_intelligence',
      read: 'read_intelligence',
      update: 'update_intelligence',
      delete: 'delete_intelligence',
      listIntelligence: 'list_intelligence'
    }
    return serviceAlpha.stdPostFunction(
      intelligenceAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}


const webCacheAPI = 'api/rubicon_admin/web_cache/'
const webCache = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'create_web_clean_cache',
      read: 'read_web_clean_cache',
      update: 'update_web_clean_cache',
      delete: 'delete_web_clean_cache',
      createReferenceRag: 'create_reference_rag',
      listUpdateTag: 'list_update_tag',
      listCreatedUpdatedBy: 'list_created_updated_by',
    }
    return serviceAlpha.stdPostFunction(
      webCacheAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}


const nerAPI = 'api/rubicon_admin/ner/'
const ner = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'create_ner',
      read: 'read_ner',
      update: 'update_ner',
      delete: 'delete_ner',
      listUpdateTag: 'list_update_tag',
      listSiteCd: 'list_site_cd',
    }
    return serviceAlpha.stdPostFunction(
      nerAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}

const productNameInferenceAPI = 'api/rubicon_admin/product_name_inference/'
const productNameInference = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'create_product_name_inference',
      read: 'read_product_name_inference',
      update: 'update_product_name_inference',
      delete: 'delete_product_name_inference',
      listUpdateTag: 'list_update_tag',
    }
    return serviceAlpha.stdPostFunction(
      productNameInferenceAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}

const unstructuredIndexAPI = 'api/rubicon_admin/unstructured_index/'
const unstructuredIndex = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'create_unstructured_index',
      read: 'read_unstructured_index',
      update: 'update_unstructured_index',
      delete: 'delete_unstructured_index',
      listOpType: 'list_op_type',
      listIndex: 'list_index'
    }
    return serviceAlpha.stdPostFunction(
      unstructuredIndexAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}

const unstructuredTestAPI = 'api/rubicon_admin/unstructured_test/'
const unstructuredTest = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      read: 'unstructured_test',
    }
    return serviceAlpha.stdPostFunction(
      unstructuredTestAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}

const specTableMetaAPI = 'api/rubicon_admin/spec_table_meta/'
const specTableMeta = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'create_spec_table_meta',
      read: 'read_spec_table_meta',
      update: 'update_spec_table_meta',
      delete: 'delete_spec_table_meta'
    }
    return serviceAlpha.stdPostFunction(
      specTableMetaAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}

const pseudoQueryAPI = 'api/rubicon_admin/pseudo_query/'
const pseudoQuery = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'create_pseudo_query',
      read: 'read_pseudo_query',
      update: 'update_pseudo_query',
      delete: 'delete_pseudo_query'
    }
    return serviceAlpha.stdPostFunction(
      pseudoQueryAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}

const virtualViewAPI = 'api/rubicon_admin/virtual_view/'
const virtualView = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'create_virtual_view',
      read: 'read_virtual_view',
      update: 'update_virtual_view',
      delete: 'delete_virtual_view',
      list: 'list_virtual_view'
    }
    return serviceAlpha.stdPostFunction(
      virtualViewAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}

const dataSourceAPI = 'api/rubicon_admin/data_source/'
const dataSource = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'create_data_source',
      read: 'read_data_source',
      update: 'update_data_source',
      delete: 'delete_data_source'
    }
    return serviceAlpha.stdPostFunction(
      dataSourceAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}

const fieldMappingAPI = 'api/rubicon_admin/field_mapping/'
const fieldMapping = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'create_field_mapping',
      read: 'read_field_mapping',
      update: 'update_field_mapping',
      delete: 'delete_field_mapping'
    }
    return serviceAlpha.stdPostFunction(
      fieldMappingAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}

const codeMappingAPI = 'api/rubicon_admin/code_mapping/'
const codeMapping = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'create_code_mapping',
      read: 'read_code_mapping',
      update: 'update_code_mapping',
      delete: 'delete_code_mapping',
      listField: 'list_distint_field_list',
    }
    return serviceAlpha.stdPostFunction(
      codeMappingAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}

const complementationCodeMappingAPI = 'api/rubicon_admin/complementation_code_mapping/'
const complementationCodeMapping = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'create_code_mapping',
      read: 'read_code_mapping',
      update: 'update_code_mapping',
      delete: 'delete_code_mapping',
      listField: 'list_distinct_field_list',
      listType: 'list_type',
      listUpdateTag: 'list_update_tag',
      listProductCategoryLv1: 'list_category_lv1',
      listProductCategoryLv2: 'list_category_lv2',
      listProductCategoryLv3: 'list_category_lv3',
    }
    return serviceAlpha.stdPostFunction(
      complementationCodeMappingAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}

const complementDbSearchAPI = 'api/rubicon_admin/complement_db_search/'
const complementDbSearch = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      read: 'complement_check_db',
      listProductCategoryLv1: 'list_category_lv1',
      listProductCategoryLv2: 'list_category_lv2',
      listProductCategoryLv3: 'list_category_lv3',
    }
    return serviceAlpha.stdPostFunction(
      complementDbSearchAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}

const complementationCodeMappingExtendedAPI = 'api/rubicon_admin/complementation_code_mapping_extended/'
const complementationCodeMappingExtended = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'create_code_mapping_extended',
      read: 'read_code_mapping_extended',
      update: 'update_code_mapping_extended',
      delete: 'delete_code_mapping_extended',
      listEdge: 'list_distinct_edge_list',
      listUpdateTag: 'list_update_tag',
      listCategoryLv1: 'list_category_lv1',
      listCategoryLv2: 'list_category_lv2',
      listCategoryLv3: 'list_category_lv3',
    }
    return serviceAlpha.stdPostFunction(
      complementationCodeMappingExtendedAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}

const complementationCodeMappingL4API = 'api/rubicon_admin/complementation_code_mapping_l4/'
const complementationCodeMappingL4 = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'create_code_mapping_l4',
      read: 'read_code_mapping_l4',
      update: 'update_code_mapping_l4',
      delete: 'delete_code_mapping_l4',
      listUpdateTag: 'list_update_tag',
      listCategoryLv1: 'list_category_lv1',
      listCategoryLv2: 'list_category_lv2',
      listCategoryLv3: 'list_category_lv3',
    }
    return serviceAlpha.stdPostFunction(
      complementationCodeMappingL4API,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}


const promptTemplateAPI = 'api/rubicon_admin/prompt_template/'
const promptTemplate = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'create_prompt_template',
      read: 'read_prompt_template',
      update: 'update_prompt_template',
      delete: 'delete_prompt_template',
      listResponseType: 'list_response_type',
      listCategoryLv1: 'list_category_lv1',
      listCategoryLv2: 'list_category_lv2',
    }
    return serviceAlpha.stdPostFunction(
      promptTemplateAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}


const hyperParameterAPI = 'api/rubicon_admin/hyper_parameter/'
const hyperParameter = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'create_hyper_parameter',
      read: 'read_hyper_parameter',
      update: 'update_hyper_parameter',
      delete: 'delete_hyper_parameter'
    }
    return serviceAlpha.stdPostFunction(
      hyperParameterAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}


const dashboardAPI = 'api/rubicon_admin/dashboard/'
const dashboard = {
  status: (action, query = {}, paging = {}) => {
    const functionMap = {
      api_call_count: 'api_call_count',
    }
    return serviceAlpha.stdPostFunction(
      dashboardAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}


const appraisalCheckAPI = 'api/rubicon_admin/appraisal_check/'
const appraisalCheck = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      read: 'read',
      resolve: 'resolve',
      check_log: 'check_log',
    }
    return serviceAlpha.stdPostFunction(
      appraisalCheckAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}

const chatAPI = 'api/rubicon_admin/chat/'
const chat = {
  function: (action, query = {}, paging = {}) => {
    const functionMap = {
      get_chat_history: 'get_chat_history',
    }
    return serviceAlpha.stdPostFunction(
      chatAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}


const testQueryAPI = 'api/rubicon_admin/test_query/'
const testQuery = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'create_test_query',
      read: 'read_test_query',
      update: 'update_test_query',
      delete: 'delete_test_query',
      list_case: 'list_case',
      create_test_case: 'create_test_case',
      translate: 'translate',
    }
    return serviceAlpha.stdPostFunction(
      testQueryAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}


const chatTestAPI = 'api/rubicon_admin/chat_test/'
const chatTest = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'create_chat_test',
      read: 'read_chat_test',
      delete: 'delete_chat_test',
      delete_case: 'delete_case',
      list_test_id: 'list_test_id',
      chat_test: 'chat_test',
      delete_chat_test: 'delete_chat_test',
    }
    return serviceAlpha.stdPostFunction(
      chatTestAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}


const managedWordAPI = 'api/rubicon_admin/managed_word/'
const managedWord = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'create_managed_word',
      read: 'read_managed_word',
      update: 'update_managed_word',
      delete: 'delete_managed_word',
      list_module: 'list_module',
      list_type: 'list_type',
      list_processing: 'list_processing',
      list_update_tag: 'list_update_tag',
    }
    return serviceAlpha.stdPostFunction(
      managedWordAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}


const privacyAPI = 'api/rubicon_admin/privacy/'
const privacy = {
  function: (action, query = {}, paging = {}) => {
    const functionMap = {
      checkPrivacy: 'check_privacy',
      getTicketGatekeeper: 'get_ticket_gatekeeper',
      processTicketGatekeeper: 'process_ticket_gatekeeper',
      getLogsByIdsGatekeeper: 'get_logs_by_ids_gatekeeper',
      getSpecificTicketGatekeeper: 'get_specific_ticket_gatekeeper',
      hideMessages: 'hide_messages_gatekeeper',
      unhideMessages: 'unhide_messages_gatekeeper',
      deleteMessages: 'delete_messages_gatekeeper',
      exportMessages: 'export_messages_gatekeeper'
    }
    return serviceAlpha.stdPostFunction(
      privacyAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}


const cptMappingDataAPI = 'api/rubicon_admin/cpt_mapping_data/'
const cptMappingData = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      // create: 'create_cpt_mapping_data',
      read: 'read_cpt_mapping_data',
      addCPTKeyword: 'insert_cpt_keyword',
    }
    return serviceAlpha.stdPostFunction(
      cptMappingDataAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}

const cptUpdDelDataAPI = 'api/rubicon_admin/cpt_upd_del_data/'
const cptUpdDelData = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      // create: 'create_cpt_upd_del_data',
      read: 'read_cpt_upd_del_data',
      updCPTKeyword: 'update_cpt_upd_del_data',
      delCPTKeyword: 'delete_cpt_upd_del_data'
    }
    return serviceAlpha.stdPostFunction(
      cptUpdDelDataAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}

const productSearchAPI = 'api/rubicon_admin/product_search/'
const productSearch = {
  table: (action, query = {}, paging = {}) => {
    const functionMap = {
      read: 'read_product_search',
    }
    return serviceAlpha.stdPostFunction(
      productSearchAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}

export const rubiconAdmin = {
  assistantProduct: assistantProduct,
  assistantRefInfo: assistantRefInfo,
  predefined: predefined,
  predefinedRAG: predefinedRAG,
  managedResponse: managedResponse,
  intelligence: intelligence,
  webCache: webCache,
  ner: ner,
  productNameInference: productNameInference,
  unstructuredIndex: unstructuredIndex,
  unstructuredTest: unstructuredTest,
  specTableMeta: specTableMeta,
  pseudoQuery: pseudoQuery,
  dataSource: dataSource,
  fieldMapping: fieldMapping,
  codeMapping: codeMapping,
  complementationCodeMapping: complementationCodeMapping,
  complementDbSearch: complementDbSearch,
  complementationCodeMappingExtended: complementationCodeMappingExtended,
  complementationCodeMappingL4: complementationCodeMappingL4,
  promptTemplate: promptTemplate,
  hyperParameter: hyperParameter,
  dashboard: dashboard,
  appraisalCheck: appraisalCheck,
  chat: chat,
  chatTest: chatTest,
  testQuery: testQuery,
  managedWord: managedWord,
  privacy: privacy,
  cptMappingData: cptMappingData,
  cptUpdDelData: cptUpdDelData,
  productSearch: productSearch
}
