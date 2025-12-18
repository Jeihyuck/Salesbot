export const template = {
  disabled: {
    NONE: () => { return false },
    NOT_CREATE: (editType) => { return editType !== 'CREATE' },
    NOT_EDIT: (editType) => { return editType !== 'EDIT' },
    ALWAYS: () => { return true }
  },
  hide: {
    ALWAYS: () => { return true }
  },
  fields: {
    REQUIRED_NUMBER: (name, disabled) => {
      return simpleNumber(name, disabled, true)
    },
    OPTIONAL_NUMBER: (name, disabled) => {
      return simpleNumber(name, disabled, false)
    },
    REQUIRED_INPUT: (name, disabled) => {
      return simpleInput(name, disabled, true)
    },
    OPTIONAL_INPUT: (name, disabled) => {
      return simpleInput(name, disabled, false)
    },
    REQUIRED_BOOLEAN: (name, disabled, defaultValue) => {
      return simpleBoolean(name, disabled, true, defaultValue)
    },
    OPTIONAL_BOOLEAN: (name, disabled, defaultValue) => {
      return simpleBoolean(name, disabled, false, defaultValue)
    },
    REQUIRED_DATEPICKER: (name, disabled, defaultValue) => {
      return simpleDatePicker(name, disabled, true, defaultValue)
    },
    OPTIONAL_DATEPICKER: (name, disabled, defaultValue) => {
      return simpleDatePicker(name, disabled, false, defaultValue)
    }
  }
}

const simpleInput = (name, disabled, required) => {
  return {
    name: name,
    type: 'input',
    disabled: disabled || template.disabled.NONE,
    required: required,
    selected: ''
  }
}

const simpleNumber = (name, disabled, required) => {
  return {
    name: name,
    type: 'input',
    number: true,
    disabled: disabled || template.disabled.NONE,
    required: required,
    selected: 0
  }
}

const simpleBoolean = (name, disabled, required, defaultValue) => {
  return {
    name: name,
    type: 'checkbox',
    disabled: disabled || template.disabled.NONE,
    required: required,
    selected: !!defaultValue
  }
}

const simpleDatePicker = (name, disabled, required, defaultValue) => {
  return {
    name: name,
    type: 'datepicker',
    menu: false, // true : show calender
    disabled: disabled || template.disabled.NONE,
    required: required,
    selected: defaultValue ?? ''
  }
}
