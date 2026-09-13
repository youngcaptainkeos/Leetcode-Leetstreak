"use strict";
(() => {
  var __create = Object.create;
  var __defProp = Object.defineProperty;
  var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __getProtoOf = Object.getPrototypeOf;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __commonJS = (cb, mod) => function __require() {
    try {
      return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
    } catch (e) {
      throw mod = 0, e;
    }
  };
  var __copyProps = (to, from, except, desc) => {
    if (from && typeof from === "object" || typeof from === "function") {
      for (let key of __getOwnPropNames(from))
        if (!__hasOwnProp.call(to, key) && key !== except)
          __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
    }
    return to;
  };
  var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
    // If the importer is in node compatibility mode or this is not an ESM
    // file that has been converted to a CommonJS file using a Babel-
    // compatible transform (i.e. "__esModule" has not been set), then set
    // "default" to the CommonJS "module.exports" for node compatibility.
    isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
    mod
  ));

  // node_modules/react/cjs/react.development.js
  var require_react_development = __commonJS({
    "node_modules/react/cjs/react.development.js"(exports, module) {
      "use strict";
      if (true) {
        (function() {
          "use strict";
          if (typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ !== "undefined" && typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.registerInternalModuleStart === "function") {
            __REACT_DEVTOOLS_GLOBAL_HOOK__.registerInternalModuleStart(new Error());
          }
          var ReactVersion = "18.3.1";
          var REACT_ELEMENT_TYPE = /* @__PURE__ */ Symbol.for("react.element");
          var REACT_PORTAL_TYPE = /* @__PURE__ */ Symbol.for("react.portal");
          var REACT_FRAGMENT_TYPE = /* @__PURE__ */ Symbol.for("react.fragment");
          var REACT_STRICT_MODE_TYPE = /* @__PURE__ */ Symbol.for("react.strict_mode");
          var REACT_PROFILER_TYPE = /* @__PURE__ */ Symbol.for("react.profiler");
          var REACT_PROVIDER_TYPE = /* @__PURE__ */ Symbol.for("react.provider");
          var REACT_CONTEXT_TYPE = /* @__PURE__ */ Symbol.for("react.context");
          var REACT_FORWARD_REF_TYPE = /* @__PURE__ */ Symbol.for("react.forward_ref");
          var REACT_SUSPENSE_TYPE = /* @__PURE__ */ Symbol.for("react.suspense");
          var REACT_SUSPENSE_LIST_TYPE = /* @__PURE__ */ Symbol.for("react.suspense_list");
          var REACT_MEMO_TYPE = /* @__PURE__ */ Symbol.for("react.memo");
          var REACT_LAZY_TYPE = /* @__PURE__ */ Symbol.for("react.lazy");
          var REACT_OFFSCREEN_TYPE = /* @__PURE__ */ Symbol.for("react.offscreen");
          var MAYBE_ITERATOR_SYMBOL = Symbol.iterator;
          var FAUX_ITERATOR_SYMBOL = "@@iterator";
          function getIteratorFn(maybeIterable) {
            if (maybeIterable === null || typeof maybeIterable !== "object") {
              return null;
            }
            var maybeIterator = MAYBE_ITERATOR_SYMBOL && maybeIterable[MAYBE_ITERATOR_SYMBOL] || maybeIterable[FAUX_ITERATOR_SYMBOL];
            if (typeof maybeIterator === "function") {
              return maybeIterator;
            }
            return null;
          }
          var ReactCurrentDispatcher = {
            /**
             * @internal
             * @type {ReactComponent}
             */
            current: null
          };
          var ReactCurrentBatchConfig = {
            transition: null
          };
          var ReactCurrentActQueue = {
            current: null,
            // Used to reproduce behavior of `batchedUpdates` in legacy mode.
            isBatchingLegacy: false,
            didScheduleLegacyUpdate: false
          };
          var ReactCurrentOwner = {
            /**
             * @internal
             * @type {ReactComponent}
             */
            current: null
          };
          var ReactDebugCurrentFrame = {};
          var currentExtraStackFrame = null;
          function setExtraStackFrame(stack) {
            {
              currentExtraStackFrame = stack;
            }
          }
          {
            ReactDebugCurrentFrame.setExtraStackFrame = function(stack) {
              {
                currentExtraStackFrame = stack;
              }
            };
            ReactDebugCurrentFrame.getCurrentStack = null;
            ReactDebugCurrentFrame.getStackAddendum = function() {
              var stack = "";
              if (currentExtraStackFrame) {
                stack += currentExtraStackFrame;
              }
              var impl = ReactDebugCurrentFrame.getCurrentStack;
              if (impl) {
                stack += impl() || "";
              }
              return stack;
            };
          }
          var enableScopeAPI = false;
          var enableCacheElement = false;
          var enableTransitionTracing = false;
          var enableLegacyHidden = false;
          var enableDebugTracing = false;
          var ReactSharedInternals = {
            ReactCurrentDispatcher,
            ReactCurrentBatchConfig,
            ReactCurrentOwner
          };
          {
            ReactSharedInternals.ReactDebugCurrentFrame = ReactDebugCurrentFrame;
            ReactSharedInternals.ReactCurrentActQueue = ReactCurrentActQueue;
          }
          function warn(format) {
            {
              {
                for (var _len = arguments.length, args = new Array(_len > 1 ? _len - 1 : 0), _key = 1; _key < _len; _key++) {
                  args[_key - 1] = arguments[_key];
                }
                printWarning("warn", format, args);
              }
            }
          }
          function error(format) {
            {
              {
                for (var _len2 = arguments.length, args = new Array(_len2 > 1 ? _len2 - 1 : 0), _key2 = 1; _key2 < _len2; _key2++) {
                  args[_key2 - 1] = arguments[_key2];
                }
                printWarning("error", format, args);
              }
            }
          }
          function printWarning(level, format, args) {
            {
              var ReactDebugCurrentFrame2 = ReactSharedInternals.ReactDebugCurrentFrame;
              var stack = ReactDebugCurrentFrame2.getStackAddendum();
              if (stack !== "") {
                format += "%s";
                args = args.concat([stack]);
              }
              var argsWithFormat = args.map(function(item) {
                return String(item);
              });
              argsWithFormat.unshift("Warning: " + format);
              Function.prototype.apply.call(console[level], console, argsWithFormat);
            }
          }
          var didWarnStateUpdateForUnmountedComponent = {};
          function warnNoop(publicInstance, callerName) {
            {
              var _constructor = publicInstance.constructor;
              var componentName = _constructor && (_constructor.displayName || _constructor.name) || "ReactClass";
              var warningKey = componentName + "." + callerName;
              if (didWarnStateUpdateForUnmountedComponent[warningKey]) {
                return;
              }
              error("Can't call %s on a component that is not yet mounted. This is a no-op, but it might indicate a bug in your application. Instead, assign to `this.state` directly or define a `state = {};` class property with the desired state in the %s component.", callerName, componentName);
              didWarnStateUpdateForUnmountedComponent[warningKey] = true;
            }
          }
          var ReactNoopUpdateQueue = {
            /**
             * Checks whether or not this composite component is mounted.
             * @param {ReactClass} publicInstance The instance we want to test.
             * @return {boolean} True if mounted, false otherwise.
             * @protected
             * @final
             */
            isMounted: function(publicInstance) {
              return false;
            },
            /**
             * Forces an update. This should only be invoked when it is known with
             * certainty that we are **not** in a DOM transaction.
             *
             * You may want to call this when you know that some deeper aspect of the
             * component's state has changed but `setState` was not called.
             *
             * This will not invoke `shouldComponentUpdate`, but it will invoke
             * `componentWillUpdate` and `componentDidUpdate`.
             *
             * @param {ReactClass} publicInstance The instance that should rerender.
             * @param {?function} callback Called after component is updated.
             * @param {?string} callerName name of the calling function in the public API.
             * @internal
             */
            enqueueForceUpdate: function(publicInstance, callback, callerName) {
              warnNoop(publicInstance, "forceUpdate");
            },
            /**
             * Replaces all of the state. Always use this or `setState` to mutate state.
             * You should treat `this.state` as immutable.
             *
             * There is no guarantee that `this.state` will be immediately updated, so
             * accessing `this.state` after calling this method may return the old value.
             *
             * @param {ReactClass} publicInstance The instance that should rerender.
             * @param {object} completeState Next state.
             * @param {?function} callback Called after component is updated.
             * @param {?string} callerName name of the calling function in the public API.
             * @internal
             */
            enqueueReplaceState: function(publicInstance, completeState, callback, callerName) {
              warnNoop(publicInstance, "replaceState");
            },
            /**
             * Sets a subset of the state. This only exists because _pendingState is
             * internal. This provides a merging strategy that is not available to deep
             * properties which is confusing. TODO: Expose pendingState or don't use it
             * during the merge.
             *
             * @param {ReactClass} publicInstance The instance that should rerender.
             * @param {object} partialState Next partial state to be merged with state.
             * @param {?function} callback Called after component is updated.
             * @param {?string} Name of the calling function in the public API.
             * @internal
             */
            enqueueSetState: function(publicInstance, partialState, callback, callerName) {
              warnNoop(publicInstance, "setState");
            }
          };
          var assign = Object.assign;
          var emptyObject = {};
          {
            Object.freeze(emptyObject);
          }
          function Component(props, context, updater) {
            this.props = props;
            this.context = context;
            this.refs = emptyObject;
            this.updater = updater || ReactNoopUpdateQueue;
          }
          Component.prototype.isReactComponent = {};
          Component.prototype.setState = function(partialState, callback) {
            if (typeof partialState !== "object" && typeof partialState !== "function" && partialState != null) {
              throw new Error("setState(...): takes an object of state variables to update or a function which returns an object of state variables.");
            }
            this.updater.enqueueSetState(this, partialState, callback, "setState");
          };
          Component.prototype.forceUpdate = function(callback) {
            this.updater.enqueueForceUpdate(this, callback, "forceUpdate");
          };
          {
            var deprecatedAPIs = {
              isMounted: ["isMounted", "Instead, make sure to clean up subscriptions and pending requests in componentWillUnmount to prevent memory leaks."],
              replaceState: ["replaceState", "Refactor your code to use setState instead (see https://github.com/facebook/react/issues/3236)."]
            };
            var defineDeprecationWarning = function(methodName, info) {
              Object.defineProperty(Component.prototype, methodName, {
                get: function() {
                  warn("%s(...) is deprecated in plain JavaScript React classes. %s", info[0], info[1]);
                  return void 0;
                }
              });
            };
            for (var fnName in deprecatedAPIs) {
              if (deprecatedAPIs.hasOwnProperty(fnName)) {
                defineDeprecationWarning(fnName, deprecatedAPIs[fnName]);
              }
            }
          }
          function ComponentDummy() {
          }
          ComponentDummy.prototype = Component.prototype;
          function PureComponent(props, context, updater) {
            this.props = props;
            this.context = context;
            this.refs = emptyObject;
            this.updater = updater || ReactNoopUpdateQueue;
          }
          var pureComponentPrototype = PureComponent.prototype = new ComponentDummy();
          pureComponentPrototype.constructor = PureComponent;
          assign(pureComponentPrototype, Component.prototype);
          pureComponentPrototype.isPureReactComponent = true;
          function createRef() {
            var refObject = {
              current: null
            };
            {
              Object.seal(refObject);
            }
            return refObject;
          }
          var isArrayImpl = Array.isArray;
          function isArray(a) {
            return isArrayImpl(a);
          }
          function typeName(value) {
            {
              var hasToStringTag = typeof Symbol === "function" && Symbol.toStringTag;
              var type = hasToStringTag && value[Symbol.toStringTag] || value.constructor.name || "Object";
              return type;
            }
          }
          function willCoercionThrow(value) {
            {
              try {
                testStringCoercion(value);
                return false;
              } catch (e) {
                return true;
              }
            }
          }
          function testStringCoercion(value) {
            return "" + value;
          }
          function checkKeyStringCoercion(value) {
            {
              if (willCoercionThrow(value)) {
                error("The provided key is an unsupported type %s. This value must be coerced to a string before before using it here.", typeName(value));
                return testStringCoercion(value);
              }
            }
          }
          function getWrappedName(outerType, innerType, wrapperName) {
            var displayName = outerType.displayName;
            if (displayName) {
              return displayName;
            }
            var functionName = innerType.displayName || innerType.name || "";
            return functionName !== "" ? wrapperName + "(" + functionName + ")" : wrapperName;
          }
          function getContextName(type) {
            return type.displayName || "Context";
          }
          function getComponentNameFromType(type) {
            if (type == null) {
              return null;
            }
            {
              if (typeof type.tag === "number") {
                error("Received an unexpected object in getComponentNameFromType(). This is likely a bug in React. Please file an issue.");
              }
            }
            if (typeof type === "function") {
              return type.displayName || type.name || null;
            }
            if (typeof type === "string") {
              return type;
            }
            switch (type) {
              case REACT_FRAGMENT_TYPE:
                return "Fragment";
              case REACT_PORTAL_TYPE:
                return "Portal";
              case REACT_PROFILER_TYPE:
                return "Profiler";
              case REACT_STRICT_MODE_TYPE:
                return "StrictMode";
              case REACT_SUSPENSE_TYPE:
                return "Suspense";
              case REACT_SUSPENSE_LIST_TYPE:
                return "SuspenseList";
            }
            if (typeof type === "object") {
              switch (type.$$typeof) {
                case REACT_CONTEXT_TYPE:
                  var context = type;
                  return getContextName(context) + ".Consumer";
                case REACT_PROVIDER_TYPE:
                  var provider = type;
                  return getContextName(provider._context) + ".Provider";
                case REACT_FORWARD_REF_TYPE:
                  return getWrappedName(type, type.render, "ForwardRef");
                case REACT_MEMO_TYPE:
                  var outerName = type.displayName || null;
                  if (outerName !== null) {
                    return outerName;
                  }
                  return getComponentNameFromType(type.type) || "Memo";
                case REACT_LAZY_TYPE: {
                  var lazyComponent = type;
                  var payload = lazyComponent._payload;
                  var init = lazyComponent._init;
                  try {
                    return getComponentNameFromType(init(payload));
                  } catch (x) {
                    return null;
                  }
                }
              }
            }
            return null;
          }
          var hasOwnProperty = Object.prototype.hasOwnProperty;
          var RESERVED_PROPS = {
            key: true,
            ref: true,
            __self: true,
            __source: true
          };
          var specialPropKeyWarningShown, specialPropRefWarningShown, didWarnAboutStringRefs;
          {
            didWarnAboutStringRefs = {};
          }
          function hasValidRef(config) {
            {
              if (hasOwnProperty.call(config, "ref")) {
                var getter = Object.getOwnPropertyDescriptor(config, "ref").get;
                if (getter && getter.isReactWarning) {
                  return false;
                }
              }
            }
            return config.ref !== void 0;
          }
          function hasValidKey(config) {
            {
              if (hasOwnProperty.call(config, "key")) {
                var getter = Object.getOwnPropertyDescriptor(config, "key").get;
                if (getter && getter.isReactWarning) {
                  return false;
                }
              }
            }
            return config.key !== void 0;
          }
          function defineKeyPropWarningGetter(props, displayName) {
            var warnAboutAccessingKey = function() {
              {
                if (!specialPropKeyWarningShown) {
                  specialPropKeyWarningShown = true;
                  error("%s: `key` is not a prop. Trying to access it will result in `undefined` being returned. If you need to access the same value within the child component, you should pass it as a different prop. (https://reactjs.org/link/special-props)", displayName);
                }
              }
            };
            warnAboutAccessingKey.isReactWarning = true;
            Object.defineProperty(props, "key", {
              get: warnAboutAccessingKey,
              configurable: true
            });
          }
          function defineRefPropWarningGetter(props, displayName) {
            var warnAboutAccessingRef = function() {
              {
                if (!specialPropRefWarningShown) {
                  specialPropRefWarningShown = true;
                  error("%s: `ref` is not a prop. Trying to access it will result in `undefined` being returned. If you need to access the same value within the child component, you should pass it as a different prop. (https://reactjs.org/link/special-props)", displayName);
                }
              }
            };
            warnAboutAccessingRef.isReactWarning = true;
            Object.defineProperty(props, "ref", {
              get: warnAboutAccessingRef,
              configurable: true
            });
          }
          function warnIfStringRefCannotBeAutoConverted(config) {
            {
              if (typeof config.ref === "string" && ReactCurrentOwner.current && config.__self && ReactCurrentOwner.current.stateNode !== config.__self) {
                var componentName = getComponentNameFromType(ReactCurrentOwner.current.type);
                if (!didWarnAboutStringRefs[componentName]) {
                  error('Component "%s" contains the string ref "%s". Support for string refs will be removed in a future major release. This case cannot be automatically converted to an arrow function. We ask you to manually fix this case by using useRef() or createRef() instead. Learn more about using refs safely here: https://reactjs.org/link/strict-mode-string-ref', componentName, config.ref);
                  didWarnAboutStringRefs[componentName] = true;
                }
              }
            }
          }
          var ReactElement = function(type, key, ref, self, source, owner, props) {
            var element = {
              // This tag allows us to uniquely identify this as a React Element
              $$typeof: REACT_ELEMENT_TYPE,
              // Built-in properties that belong on the element
              type,
              key,
              ref,
              props,
              // Record the component responsible for creating this element.
              _owner: owner
            };
            {
              element._store = {};
              Object.defineProperty(element._store, "validated", {
                configurable: false,
                enumerable: false,
                writable: true,
                value: false
              });
              Object.defineProperty(element, "_self", {
                configurable: false,
                enumerable: false,
                writable: false,
                value: self
              });
              Object.defineProperty(element, "_source", {
                configurable: false,
                enumerable: false,
                writable: false,
                value: source
              });
              if (Object.freeze) {
                Object.freeze(element.props);
                Object.freeze(element);
              }
            }
            return element;
          };
          function createElement(type, config, children) {
            var propName;
            var props = {};
            var key = null;
            var ref = null;
            var self = null;
            var source = null;
            if (config != null) {
              if (hasValidRef(config)) {
                ref = config.ref;
                {
                  warnIfStringRefCannotBeAutoConverted(config);
                }
              }
              if (hasValidKey(config)) {
                {
                  checkKeyStringCoercion(config.key);
                }
                key = "" + config.key;
              }
              self = config.__self === void 0 ? null : config.__self;
              source = config.__source === void 0 ? null : config.__source;
              for (propName in config) {
                if (hasOwnProperty.call(config, propName) && !RESERVED_PROPS.hasOwnProperty(propName)) {
                  props[propName] = config[propName];
                }
              }
            }
            var childrenLength = arguments.length - 2;
            if (childrenLength === 1) {
              props.children = children;
            } else if (childrenLength > 1) {
              var childArray = Array(childrenLength);
              for (var i = 0; i < childrenLength; i++) {
                childArray[i] = arguments[i + 2];
              }
              {
                if (Object.freeze) {
                  Object.freeze(childArray);
                }
              }
              props.children = childArray;
            }
            if (type && type.defaultProps) {
              var defaultProps = type.defaultProps;
              for (propName in defaultProps) {
                if (props[propName] === void 0) {
                  props[propName] = defaultProps[propName];
                }
              }
            }
            {
              if (key || ref) {
                var displayName = typeof type === "function" ? type.displayName || type.name || "Unknown" : type;
                if (key) {
                  defineKeyPropWarningGetter(props, displayName);
                }
                if (ref) {
                  defineRefPropWarningGetter(props, displayName);
                }
              }
            }
            return ReactElement(type, key, ref, self, source, ReactCurrentOwner.current, props);
          }
          function cloneAndReplaceKey(oldElement, newKey) {
            var newElement = ReactElement(oldElement.type, newKey, oldElement.ref, oldElement._self, oldElement._source, oldElement._owner, oldElement.props);
            return newElement;
          }
          function cloneElement(element, config, children) {
            if (element === null || element === void 0) {
              throw new Error("React.cloneElement(...): The argument must be a React element, but you passed " + element + ".");
            }
            var propName;
            var props = assign({}, element.props);
            var key = element.key;
            var ref = element.ref;
            var self = element._self;
            var source = element._source;
            var owner = element._owner;
            if (config != null) {
              if (hasValidRef(config)) {
                ref = config.ref;
                owner = ReactCurrentOwner.current;
              }
              if (hasValidKey(config)) {
                {
                  checkKeyStringCoercion(config.key);
                }
                key = "" + config.key;
              }
              var defaultProps;
              if (element.type && element.type.defaultProps) {
                defaultProps = element.type.defaultProps;
              }
              for (propName in config) {
                if (hasOwnProperty.call(config, propName) && !RESERVED_PROPS.hasOwnProperty(propName)) {
                  if (config[propName] === void 0 && defaultProps !== void 0) {
                    props[propName] = defaultProps[propName];
                  } else {
                    props[propName] = config[propName];
                  }
                }
              }
            }
            var childrenLength = arguments.length - 2;
            if (childrenLength === 1) {
              props.children = children;
            } else if (childrenLength > 1) {
              var childArray = Array(childrenLength);
              for (var i = 0; i < childrenLength; i++) {
                childArray[i] = arguments[i + 2];
              }
              props.children = childArray;
            }
            return ReactElement(element.type, key, ref, self, source, owner, props);
          }
          function isValidElement(object) {
            return typeof object === "object" && object !== null && object.$$typeof === REACT_ELEMENT_TYPE;
          }
          var SEPARATOR = ".";
          var SUBSEPARATOR = ":";
          function escape(key) {
            var escapeRegex = /[=:]/g;
            var escaperLookup = {
              "=": "=0",
              ":": "=2"
            };
            var escapedString = key.replace(escapeRegex, function(match) {
              return escaperLookup[match];
            });
            return "$" + escapedString;
          }
          var didWarnAboutMaps = false;
          var userProvidedKeyEscapeRegex = /\/+/g;
          function escapeUserProvidedKey(text) {
            return text.replace(userProvidedKeyEscapeRegex, "$&/");
          }
          function getElementKey(element, index) {
            if (typeof element === "object" && element !== null && element.key != null) {
              {
                checkKeyStringCoercion(element.key);
              }
              return escape("" + element.key);
            }
            return index.toString(36);
          }
          function mapIntoArray(children, array, escapedPrefix, nameSoFar, callback) {
            var type = typeof children;
            if (type === "undefined" || type === "boolean") {
              children = null;
            }
            var invokeCallback = false;
            if (children === null) {
              invokeCallback = true;
            } else {
              switch (type) {
                case "string":
                case "number":
                  invokeCallback = true;
                  break;
                case "object":
                  switch (children.$$typeof) {
                    case REACT_ELEMENT_TYPE:
                    case REACT_PORTAL_TYPE:
                      invokeCallback = true;
                  }
              }
            }
            if (invokeCallback) {
              var _child = children;
              var mappedChild = callback(_child);
              var childKey = nameSoFar === "" ? SEPARATOR + getElementKey(_child, 0) : nameSoFar;
              if (isArray(mappedChild)) {
                var escapedChildKey = "";
                if (childKey != null) {
                  escapedChildKey = escapeUserProvidedKey(childKey) + "/";
                }
                mapIntoArray(mappedChild, array, escapedChildKey, "", function(c) {
                  return c;
                });
              } else if (mappedChild != null) {
                if (isValidElement(mappedChild)) {
                  {
                    if (mappedChild.key && (!_child || _child.key !== mappedChild.key)) {
                      checkKeyStringCoercion(mappedChild.key);
                    }
                  }
                  mappedChild = cloneAndReplaceKey(
                    mappedChild,
                    // Keep both the (mapped) and old keys if they differ, just as
                    // traverseAllChildren used to do for objects as children
                    escapedPrefix + // $FlowFixMe Flow incorrectly thinks React.Portal doesn't have a key
                    (mappedChild.key && (!_child || _child.key !== mappedChild.key) ? (
                      // $FlowFixMe Flow incorrectly thinks existing element's key can be a number
                      // eslint-disable-next-line react-internal/safe-string-coercion
                      escapeUserProvidedKey("" + mappedChild.key) + "/"
                    ) : "") + childKey
                  );
                }
                array.push(mappedChild);
              }
              return 1;
            }
            var child;
            var nextName;
            var subtreeCount = 0;
            var nextNamePrefix = nameSoFar === "" ? SEPARATOR : nameSoFar + SUBSEPARATOR;
            if (isArray(children)) {
              for (var i = 0; i < children.length; i++) {
                child = children[i];
                nextName = nextNamePrefix + getElementKey(child, i);
                subtreeCount += mapIntoArray(child, array, escapedPrefix, nextName, callback);
              }
            } else {
              var iteratorFn = getIteratorFn(children);
              if (typeof iteratorFn === "function") {
                var iterableChildren = children;
                {
                  if (iteratorFn === iterableChildren.entries) {
                    if (!didWarnAboutMaps) {
                      warn("Using Maps as children is not supported. Use an array of keyed ReactElements instead.");
                    }
                    didWarnAboutMaps = true;
                  }
                }
                var iterator = iteratorFn.call(iterableChildren);
                var step;
                var ii = 0;
                while (!(step = iterator.next()).done) {
                  child = step.value;
                  nextName = nextNamePrefix + getElementKey(child, ii++);
                  subtreeCount += mapIntoArray(child, array, escapedPrefix, nextName, callback);
                }
              } else if (type === "object") {
                var childrenString = String(children);
                throw new Error("Objects are not valid as a React child (found: " + (childrenString === "[object Object]" ? "object with keys {" + Object.keys(children).join(", ") + "}" : childrenString) + "). If you meant to render a collection of children, use an array instead.");
              }
            }
            return subtreeCount;
          }
          function mapChildren(children, func, context) {
            if (children == null) {
              return children;
            }
            var result = [];
            var count = 0;
            mapIntoArray(children, result, "", "", function(child) {
              return func.call(context, child, count++);
            });
            return result;
          }
          function countChildren(children) {
            var n = 0;
            mapChildren(children, function() {
              n++;
            });
            return n;
          }
          function forEachChildren(children, forEachFunc, forEachContext) {
            mapChildren(children, function() {
              forEachFunc.apply(this, arguments);
            }, forEachContext);
          }
          function toArray(children) {
            return mapChildren(children, function(child) {
              return child;
            }) || [];
          }
          function onlyChild(children) {
            if (!isValidElement(children)) {
              throw new Error("React.Children.only expected to receive a single React element child.");
            }
            return children;
          }
          function createContext(defaultValue) {
            var context = {
              $$typeof: REACT_CONTEXT_TYPE,
              // As a workaround to support multiple concurrent renderers, we categorize
              // some renderers as primary and others as secondary. We only expect
              // there to be two concurrent renderers at most: React Native (primary) and
              // Fabric (secondary); React DOM (primary) and React ART (secondary).
              // Secondary renderers store their context values on separate fields.
              _currentValue: defaultValue,
              _currentValue2: defaultValue,
              // Used to track how many concurrent renderers this context currently
              // supports within in a single renderer. Such as parallel server rendering.
              _threadCount: 0,
              // These are circular
              Provider: null,
              Consumer: null,
              // Add these to use same hidden class in VM as ServerContext
              _defaultValue: null,
              _globalName: null
            };
            context.Provider = {
              $$typeof: REACT_PROVIDER_TYPE,
              _context: context
            };
            var hasWarnedAboutUsingNestedContextConsumers = false;
            var hasWarnedAboutUsingConsumerProvider = false;
            var hasWarnedAboutDisplayNameOnConsumer = false;
            {
              var Consumer = {
                $$typeof: REACT_CONTEXT_TYPE,
                _context: context
              };
              Object.defineProperties(Consumer, {
                Provider: {
                  get: function() {
                    if (!hasWarnedAboutUsingConsumerProvider) {
                      hasWarnedAboutUsingConsumerProvider = true;
                      error("Rendering <Context.Consumer.Provider> is not supported and will be removed in a future major release. Did you mean to render <Context.Provider> instead?");
                    }
                    return context.Provider;
                  },
                  set: function(_Provider) {
                    context.Provider = _Provider;
                  }
                },
                _currentValue: {
                  get: function() {
                    return context._currentValue;
                  },
                  set: function(_currentValue) {
                    context._currentValue = _currentValue;
                  }
                },
                _currentValue2: {
                  get: function() {
                    return context._currentValue2;
                  },
                  set: function(_currentValue2) {
                    context._currentValue2 = _currentValue2;
                  }
                },
                _threadCount: {
                  get: function() {
                    return context._threadCount;
                  },
                  set: function(_threadCount) {
                    context._threadCount = _threadCount;
                  }
                },
                Consumer: {
                  get: function() {
                    if (!hasWarnedAboutUsingNestedContextConsumers) {
                      hasWarnedAboutUsingNestedContextConsumers = true;
                      error("Rendering <Context.Consumer.Consumer> is not supported and will be removed in a future major release. Did you mean to render <Context.Consumer> instead?");
                    }
                    return context.Consumer;
                  }
                },
                displayName: {
                  get: function() {
                    return context.displayName;
                  },
                  set: function(displayName) {
                    if (!hasWarnedAboutDisplayNameOnConsumer) {
                      warn("Setting `displayName` on Context.Consumer has no effect. You should set it directly on the context with Context.displayName = '%s'.", displayName);
                      hasWarnedAboutDisplayNameOnConsumer = true;
                    }
                  }
                }
              });
              context.Consumer = Consumer;
            }
            {
              context._currentRenderer = null;
              context._currentRenderer2 = null;
            }
            return context;
          }
          var Uninitialized = -1;
          var Pending = 0;
          var Resolved = 1;
          var Rejected = 2;
          function lazyInitializer(payload) {
            if (payload._status === Uninitialized) {
              var ctor = payload._result;
              var thenable = ctor();
              thenable.then(function(moduleObject2) {
                if (payload._status === Pending || payload._status === Uninitialized) {
                  var resolved = payload;
                  resolved._status = Resolved;
                  resolved._result = moduleObject2;
                }
              }, function(error2) {
                if (payload._status === Pending || payload._status === Uninitialized) {
                  var rejected = payload;
                  rejected._status = Rejected;
                  rejected._result = error2;
                }
              });
              if (payload._status === Uninitialized) {
                var pending = payload;
                pending._status = Pending;
                pending._result = thenable;
              }
            }
            if (payload._status === Resolved) {
              var moduleObject = payload._result;
              {
                if (moduleObject === void 0) {
                  error("lazy: Expected the result of a dynamic import() call. Instead received: %s\n\nYour code should look like: \n  const MyComponent = lazy(() => import('./MyComponent'))\n\nDid you accidentally put curly braces around the import?", moduleObject);
                }
              }
              {
                if (!("default" in moduleObject)) {
                  error("lazy: Expected the result of a dynamic import() call. Instead received: %s\n\nYour code should look like: \n  const MyComponent = lazy(() => import('./MyComponent'))", moduleObject);
                }
              }
              return moduleObject.default;
            } else {
              throw payload._result;
            }
          }
          function lazy(ctor) {
            var payload = {
              // We use these fields to store the result.
              _status: Uninitialized,
              _result: ctor
            };
            var lazyType = {
              $$typeof: REACT_LAZY_TYPE,
              _payload: payload,
              _init: lazyInitializer
            };
            {
              var defaultProps;
              var propTypes;
              Object.defineProperties(lazyType, {
                defaultProps: {
                  configurable: true,
                  get: function() {
                    return defaultProps;
                  },
                  set: function(newDefaultProps) {
                    error("React.lazy(...): It is not supported to assign `defaultProps` to a lazy component import. Either specify them where the component is defined, or create a wrapping component around it.");
                    defaultProps = newDefaultProps;
                    Object.defineProperty(lazyType, "defaultProps", {
                      enumerable: true
                    });
                  }
                },
                propTypes: {
                  configurable: true,
                  get: function() {
                    return propTypes;
                  },
                  set: function(newPropTypes) {
                    error("React.lazy(...): It is not supported to assign `propTypes` to a lazy component import. Either specify them where the component is defined, or create a wrapping component around it.");
                    propTypes = newPropTypes;
                    Object.defineProperty(lazyType, "propTypes", {
                      enumerable: true
                    });
                  }
                }
              });
            }
            return lazyType;
          }
          function forwardRef(render) {
            {
              if (render != null && render.$$typeof === REACT_MEMO_TYPE) {
                error("forwardRef requires a render function but received a `memo` component. Instead of forwardRef(memo(...)), use memo(forwardRef(...)).");
              } else if (typeof render !== "function") {
                error("forwardRef requires a render function but was given %s.", render === null ? "null" : typeof render);
              } else {
                if (render.length !== 0 && render.length !== 2) {
                  error("forwardRef render functions accept exactly two parameters: props and ref. %s", render.length === 1 ? "Did you forget to use the ref parameter?" : "Any additional parameter will be undefined.");
                }
              }
              if (render != null) {
                if (render.defaultProps != null || render.propTypes != null) {
                  error("forwardRef render functions do not support propTypes or defaultProps. Did you accidentally pass a React component?");
                }
              }
            }
            var elementType = {
              $$typeof: REACT_FORWARD_REF_TYPE,
              render
            };
            {
              var ownName;
              Object.defineProperty(elementType, "displayName", {
                enumerable: false,
                configurable: true,
                get: function() {
                  return ownName;
                },
                set: function(name) {
                  ownName = name;
                  if (!render.name && !render.displayName) {
                    render.displayName = name;
                  }
                }
              });
            }
            return elementType;
          }
          var REACT_MODULE_REFERENCE;
          {
            REACT_MODULE_REFERENCE = /* @__PURE__ */ Symbol.for("react.module.reference");
          }
          function isValidElementType(type) {
            if (typeof type === "string" || typeof type === "function") {
              return true;
            }
            if (type === REACT_FRAGMENT_TYPE || type === REACT_PROFILER_TYPE || enableDebugTracing || type === REACT_STRICT_MODE_TYPE || type === REACT_SUSPENSE_TYPE || type === REACT_SUSPENSE_LIST_TYPE || enableLegacyHidden || type === REACT_OFFSCREEN_TYPE || enableScopeAPI || enableCacheElement || enableTransitionTracing) {
              return true;
            }
            if (typeof type === "object" && type !== null) {
              if (type.$$typeof === REACT_LAZY_TYPE || type.$$typeof === REACT_MEMO_TYPE || type.$$typeof === REACT_PROVIDER_TYPE || type.$$typeof === REACT_CONTEXT_TYPE || type.$$typeof === REACT_FORWARD_REF_TYPE || // This needs to include all possible module reference object
              // types supported by any Flight configuration anywhere since
              // we don't know which Flight build this will end up being used
              // with.
              type.$$typeof === REACT_MODULE_REFERENCE || type.getModuleId !== void 0) {
                return true;
              }
            }
            return false;
          }
          function memo(type, compare) {
            {
              if (!isValidElementType(type)) {
                error("memo: The first argument must be a component. Instead received: %s", type === null ? "null" : typeof type);
              }
            }
            var elementType = {
              $$typeof: REACT_MEMO_TYPE,
              type,
              compare: compare === void 0 ? null : compare
            };
            {
              var ownName;
              Object.defineProperty(elementType, "displayName", {
                enumerable: false,
                configurable: true,
                get: function() {
                  return ownName;
                },
                set: function(name) {
                  ownName = name;
                  if (!type.name && !type.displayName) {
                    type.displayName = name;
                  }
                }
              });
            }
            return elementType;
          }
          function resolveDispatcher() {
            var dispatcher = ReactCurrentDispatcher.current;
            {
              if (dispatcher === null) {
                error("Invalid hook call. Hooks can only be called inside of the body of a function component. This could happen for one of the following reasons:\n1. You might have mismatching versions of React and the renderer (such as React DOM)\n2. You might be breaking the Rules of Hooks\n3. You might have more than one copy of React in the same app\nSee https://reactjs.org/link/invalid-hook-call for tips about how to debug and fix this problem.");
              }
            }
            return dispatcher;
          }
          function useContext(Context) {
            var dispatcher = resolveDispatcher();
            {
              if (Context._context !== void 0) {
                var realContext = Context._context;
                if (realContext.Consumer === Context) {
                  error("Calling useContext(Context.Consumer) is not supported, may cause bugs, and will be removed in a future major release. Did you mean to call useContext(Context) instead?");
                } else if (realContext.Provider === Context) {
                  error("Calling useContext(Context.Provider) is not supported. Did you mean to call useContext(Context) instead?");
                }
              }
            }
            return dispatcher.useContext(Context);
          }
          function useState2(initialState) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useState(initialState);
          }
          function useReducer(reducer, initialArg, init) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useReducer(reducer, initialArg, init);
          }
          function useRef(initialValue) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useRef(initialValue);
          }
          function useEffect2(create, deps) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useEffect(create, deps);
          }
          function useInsertionEffect(create, deps) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useInsertionEffect(create, deps);
          }
          function useLayoutEffect(create, deps) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useLayoutEffect(create, deps);
          }
          function useCallback(callback, deps) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useCallback(callback, deps);
          }
          function useMemo(create, deps) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useMemo(create, deps);
          }
          function useImperativeHandle(ref, create, deps) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useImperativeHandle(ref, create, deps);
          }
          function useDebugValue(value, formatterFn) {
            {
              var dispatcher = resolveDispatcher();
              return dispatcher.useDebugValue(value, formatterFn);
            }
          }
          function useTransition() {
            var dispatcher = resolveDispatcher();
            return dispatcher.useTransition();
          }
          function useDeferredValue(value) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useDeferredValue(value);
          }
          function useId() {
            var dispatcher = resolveDispatcher();
            return dispatcher.useId();
          }
          function useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
          }
          var disabledDepth = 0;
          var prevLog;
          var prevInfo;
          var prevWarn;
          var prevError;
          var prevGroup;
          var prevGroupCollapsed;
          var prevGroupEnd;
          function disabledLog() {
          }
          disabledLog.__reactDisabledLog = true;
          function disableLogs() {
            {
              if (disabledDepth === 0) {
                prevLog = console.log;
                prevInfo = console.info;
                prevWarn = console.warn;
                prevError = console.error;
                prevGroup = console.group;
                prevGroupCollapsed = console.groupCollapsed;
                prevGroupEnd = console.groupEnd;
                var props = {
                  configurable: true,
                  enumerable: true,
                  value: disabledLog,
                  writable: true
                };
                Object.defineProperties(console, {
                  info: props,
                  log: props,
                  warn: props,
                  error: props,
                  group: props,
                  groupCollapsed: props,
                  groupEnd: props
                });
              }
              disabledDepth++;
            }
          }
          function reenableLogs() {
            {
              disabledDepth--;
              if (disabledDepth === 0) {
                var props = {
                  configurable: true,
                  enumerable: true,
                  writable: true
                };
                Object.defineProperties(console, {
                  log: assign({}, props, {
                    value: prevLog
                  }),
                  info: assign({}, props, {
                    value: prevInfo
                  }),
                  warn: assign({}, props, {
                    value: prevWarn
                  }),
                  error: assign({}, props, {
                    value: prevError
                  }),
                  group: assign({}, props, {
                    value: prevGroup
                  }),
                  groupCollapsed: assign({}, props, {
                    value: prevGroupCollapsed
                  }),
                  groupEnd: assign({}, props, {
                    value: prevGroupEnd
                  })
                });
              }
              if (disabledDepth < 0) {
                error("disabledDepth fell below zero. This is a bug in React. Please file an issue.");
              }
            }
          }
          var ReactCurrentDispatcher$1 = ReactSharedInternals.ReactCurrentDispatcher;
          var prefix;
          function describeBuiltInComponentFrame(name, source, ownerFn) {
            {
              if (prefix === void 0) {
                try {
                  throw Error();
                } catch (x) {
                  var match = x.stack.trim().match(/\n( *(at )?)/);
                  prefix = match && match[1] || "";
                }
              }
              return "\n" + prefix + name;
            }
          }
          var reentry = false;
          var componentFrameCache;
          {
            var PossiblyWeakMap = typeof WeakMap === "function" ? WeakMap : Map;
            componentFrameCache = new PossiblyWeakMap();
          }
          function describeNativeComponentFrame(fn, construct) {
            if (!fn || reentry) {
              return "";
            }
            {
              var frame = componentFrameCache.get(fn);
              if (frame !== void 0) {
                return frame;
              }
            }
            var control;
            reentry = true;
            var previousPrepareStackTrace = Error.prepareStackTrace;
            Error.prepareStackTrace = void 0;
            var previousDispatcher;
            {
              previousDispatcher = ReactCurrentDispatcher$1.current;
              ReactCurrentDispatcher$1.current = null;
              disableLogs();
            }
            try {
              if (construct) {
                var Fake = function() {
                  throw Error();
                };
                Object.defineProperty(Fake.prototype, "props", {
                  set: function() {
                    throw Error();
                  }
                });
                if (typeof Reflect === "object" && Reflect.construct) {
                  try {
                    Reflect.construct(Fake, []);
                  } catch (x) {
                    control = x;
                  }
                  Reflect.construct(fn, [], Fake);
                } else {
                  try {
                    Fake.call();
                  } catch (x) {
                    control = x;
                  }
                  fn.call(Fake.prototype);
                }
              } else {
                try {
                  throw Error();
                } catch (x) {
                  control = x;
                }
                fn();
              }
            } catch (sample) {
              if (sample && control && typeof sample.stack === "string") {
                var sampleLines = sample.stack.split("\n");
                var controlLines = control.stack.split("\n");
                var s = sampleLines.length - 1;
                var c = controlLines.length - 1;
                while (s >= 1 && c >= 0 && sampleLines[s] !== controlLines[c]) {
                  c--;
                }
                for (; s >= 1 && c >= 0; s--, c--) {
                  if (sampleLines[s] !== controlLines[c]) {
                    if (s !== 1 || c !== 1) {
                      do {
                        s--;
                        c--;
                        if (c < 0 || sampleLines[s] !== controlLines[c]) {
                          var _frame = "\n" + sampleLines[s].replace(" at new ", " at ");
                          if (fn.displayName && _frame.includes("<anonymous>")) {
                            _frame = _frame.replace("<anonymous>", fn.displayName);
                          }
                          {
                            if (typeof fn === "function") {
                              componentFrameCache.set(fn, _frame);
                            }
                          }
                          return _frame;
                        }
                      } while (s >= 1 && c >= 0);
                    }
                    break;
                  }
                }
              }
            } finally {
              reentry = false;
              {
                ReactCurrentDispatcher$1.current = previousDispatcher;
                reenableLogs();
              }
              Error.prepareStackTrace = previousPrepareStackTrace;
            }
            var name = fn ? fn.displayName || fn.name : "";
            var syntheticFrame = name ? describeBuiltInComponentFrame(name) : "";
            {
              if (typeof fn === "function") {
                componentFrameCache.set(fn, syntheticFrame);
              }
            }
            return syntheticFrame;
          }
          function describeFunctionComponentFrame(fn, source, ownerFn) {
            {
              return describeNativeComponentFrame(fn, false);
            }
          }
          function shouldConstruct(Component2) {
            var prototype = Component2.prototype;
            return !!(prototype && prototype.isReactComponent);
          }
          function describeUnknownElementTypeFrameInDEV(type, source, ownerFn) {
            if (type == null) {
              return "";
            }
            if (typeof type === "function") {
              {
                return describeNativeComponentFrame(type, shouldConstruct(type));
              }
            }
            if (typeof type === "string") {
              return describeBuiltInComponentFrame(type);
            }
            switch (type) {
              case REACT_SUSPENSE_TYPE:
                return describeBuiltInComponentFrame("Suspense");
              case REACT_SUSPENSE_LIST_TYPE:
                return describeBuiltInComponentFrame("SuspenseList");
            }
            if (typeof type === "object") {
              switch (type.$$typeof) {
                case REACT_FORWARD_REF_TYPE:
                  return describeFunctionComponentFrame(type.render);
                case REACT_MEMO_TYPE:
                  return describeUnknownElementTypeFrameInDEV(type.type, source, ownerFn);
                case REACT_LAZY_TYPE: {
                  var lazyComponent = type;
                  var payload = lazyComponent._payload;
                  var init = lazyComponent._init;
                  try {
                    return describeUnknownElementTypeFrameInDEV(init(payload), source, ownerFn);
                  } catch (x) {
                  }
                }
              }
            }
            return "";
          }
          var loggedTypeFailures = {};
          var ReactDebugCurrentFrame$1 = ReactSharedInternals.ReactDebugCurrentFrame;
          function setCurrentlyValidatingElement(element) {
            {
              if (element) {
                var owner = element._owner;
                var stack = describeUnknownElementTypeFrameInDEV(element.type, element._source, owner ? owner.type : null);
                ReactDebugCurrentFrame$1.setExtraStackFrame(stack);
              } else {
                ReactDebugCurrentFrame$1.setExtraStackFrame(null);
              }
            }
          }
          function checkPropTypes(typeSpecs, values, location, componentName, element) {
            {
              var has = Function.call.bind(hasOwnProperty);
              for (var typeSpecName in typeSpecs) {
                if (has(typeSpecs, typeSpecName)) {
                  var error$1 = void 0;
                  try {
                    if (typeof typeSpecs[typeSpecName] !== "function") {
                      var err = Error((componentName || "React class") + ": " + location + " type `" + typeSpecName + "` is invalid; it must be a function, usually from the `prop-types` package, but received `" + typeof typeSpecs[typeSpecName] + "`.This often happens because of typos such as `PropTypes.function` instead of `PropTypes.func`.");
                      err.name = "Invariant Violation";
                      throw err;
                    }
                    error$1 = typeSpecs[typeSpecName](values, typeSpecName, componentName, location, null, "SECRET_DO_NOT_PASS_THIS_OR_YOU_WILL_BE_FIRED");
                  } catch (ex) {
                    error$1 = ex;
                  }
                  if (error$1 && !(error$1 instanceof Error)) {
                    setCurrentlyValidatingElement(element);
                    error("%s: type specification of %s `%s` is invalid; the type checker function must return `null` or an `Error` but returned a %s. You may have forgotten to pass an argument to the type checker creator (arrayOf, instanceOf, objectOf, oneOf, oneOfType, and shape all require an argument).", componentName || "React class", location, typeSpecName, typeof error$1);
                    setCurrentlyValidatingElement(null);
                  }
                  if (error$1 instanceof Error && !(error$1.message in loggedTypeFailures)) {
                    loggedTypeFailures[error$1.message] = true;
                    setCurrentlyValidatingElement(element);
                    error("Failed %s type: %s", location, error$1.message);
                    setCurrentlyValidatingElement(null);
                  }
                }
              }
            }
          }
          function setCurrentlyValidatingElement$1(element) {
            {
              if (element) {
                var owner = element._owner;
                var stack = describeUnknownElementTypeFrameInDEV(element.type, element._source, owner ? owner.type : null);
                setExtraStackFrame(stack);
              } else {
                setExtraStackFrame(null);
              }
            }
          }
          var propTypesMisspellWarningShown;
          {
            propTypesMisspellWarningShown = false;
          }
          function getDeclarationErrorAddendum() {
            if (ReactCurrentOwner.current) {
              var name = getComponentNameFromType(ReactCurrentOwner.current.type);
              if (name) {
                return "\n\nCheck the render method of `" + name + "`.";
              }
            }
            return "";
          }
          function getSourceInfoErrorAddendum(source) {
            if (source !== void 0) {
              var fileName = source.fileName.replace(/^.*[\\\/]/, "");
              var lineNumber = source.lineNumber;
              return "\n\nCheck your code at " + fileName + ":" + lineNumber + ".";
            }
            return "";
          }
          function getSourceInfoErrorAddendumForProps(elementProps) {
            if (elementProps !== null && elementProps !== void 0) {
              return getSourceInfoErrorAddendum(elementProps.__source);
            }
            return "";
          }
          var ownerHasKeyUseWarning = {};
          function getCurrentComponentErrorInfo(parentType) {
            var info = getDeclarationErrorAddendum();
            if (!info) {
              var parentName = typeof parentType === "string" ? parentType : parentType.displayName || parentType.name;
              if (parentName) {
                info = "\n\nCheck the top-level render call using <" + parentName + ">.";
              }
            }
            return info;
          }
          function validateExplicitKey(element, parentType) {
            if (!element._store || element._store.validated || element.key != null) {
              return;
            }
            element._store.validated = true;
            var currentComponentErrorInfo = getCurrentComponentErrorInfo(parentType);
            if (ownerHasKeyUseWarning[currentComponentErrorInfo]) {
              return;
            }
            ownerHasKeyUseWarning[currentComponentErrorInfo] = true;
            var childOwner = "";
            if (element && element._owner && element._owner !== ReactCurrentOwner.current) {
              childOwner = " It was passed a child from " + getComponentNameFromType(element._owner.type) + ".";
            }
            {
              setCurrentlyValidatingElement$1(element);
              error('Each child in a list should have a unique "key" prop.%s%s See https://reactjs.org/link/warning-keys for more information.', currentComponentErrorInfo, childOwner);
              setCurrentlyValidatingElement$1(null);
            }
          }
          function validateChildKeys(node, parentType) {
            if (typeof node !== "object") {
              return;
            }
            if (isArray(node)) {
              for (var i = 0; i < node.length; i++) {
                var child = node[i];
                if (isValidElement(child)) {
                  validateExplicitKey(child, parentType);
                }
              }
            } else if (isValidElement(node)) {
              if (node._store) {
                node._store.validated = true;
              }
            } else if (node) {
              var iteratorFn = getIteratorFn(node);
              if (typeof iteratorFn === "function") {
                if (iteratorFn !== node.entries) {
                  var iterator = iteratorFn.call(node);
                  var step;
                  while (!(step = iterator.next()).done) {
                    if (isValidElement(step.value)) {
                      validateExplicitKey(step.value, parentType);
                    }
                  }
                }
              }
            }
          }
          function validatePropTypes(element) {
            {
              var type = element.type;
              if (type === null || type === void 0 || typeof type === "string") {
                return;
              }
              var propTypes;
              if (typeof type === "function") {
                propTypes = type.propTypes;
              } else if (typeof type === "object" && (type.$$typeof === REACT_FORWARD_REF_TYPE || // Note: Memo only checks outer props here.
              // Inner props are checked in the reconciler.
              type.$$typeof === REACT_MEMO_TYPE)) {
                propTypes = type.propTypes;
              } else {
                return;
              }
              if (propTypes) {
                var name = getComponentNameFromType(type);
                checkPropTypes(propTypes, element.props, "prop", name, element);
              } else if (type.PropTypes !== void 0 && !propTypesMisspellWarningShown) {
                propTypesMisspellWarningShown = true;
                var _name = getComponentNameFromType(type);
                error("Component %s declared `PropTypes` instead of `propTypes`. Did you misspell the property assignment?", _name || "Unknown");
              }
              if (typeof type.getDefaultProps === "function" && !type.getDefaultProps.isReactClassApproved) {
                error("getDefaultProps is only used on classic React.createClass definitions. Use a static property named `defaultProps` instead.");
              }
            }
          }
          function validateFragmentProps(fragment) {
            {
              var keys = Object.keys(fragment.props);
              for (var i = 0; i < keys.length; i++) {
                var key = keys[i];
                if (key !== "children" && key !== "key") {
                  setCurrentlyValidatingElement$1(fragment);
                  error("Invalid prop `%s` supplied to `React.Fragment`. React.Fragment can only have `key` and `children` props.", key);
                  setCurrentlyValidatingElement$1(null);
                  break;
                }
              }
              if (fragment.ref !== null) {
                setCurrentlyValidatingElement$1(fragment);
                error("Invalid attribute `ref` supplied to `React.Fragment`.");
                setCurrentlyValidatingElement$1(null);
              }
            }
          }
          function createElementWithValidation(type, props, children) {
            var validType = isValidElementType(type);
            if (!validType) {
              var info = "";
              if (type === void 0 || typeof type === "object" && type !== null && Object.keys(type).length === 0) {
                info += " You likely forgot to export your component from the file it's defined in, or you might have mixed up default and named imports.";
              }
              var sourceInfo = getSourceInfoErrorAddendumForProps(props);
              if (sourceInfo) {
                info += sourceInfo;
              } else {
                info += getDeclarationErrorAddendum();
              }
              var typeString;
              if (type === null) {
                typeString = "null";
              } else if (isArray(type)) {
                typeString = "array";
              } else if (type !== void 0 && type.$$typeof === REACT_ELEMENT_TYPE) {
                typeString = "<" + (getComponentNameFromType(type.type) || "Unknown") + " />";
                info = " Did you accidentally export a JSX literal instead of a component?";
              } else {
                typeString = typeof type;
              }
              {
                error("React.createElement: type is invalid -- expected a string (for built-in components) or a class/function (for composite components) but got: %s.%s", typeString, info);
              }
            }
            var element = createElement.apply(this, arguments);
            if (element == null) {
              return element;
            }
            if (validType) {
              for (var i = 2; i < arguments.length; i++) {
                validateChildKeys(arguments[i], type);
              }
            }
            if (type === REACT_FRAGMENT_TYPE) {
              validateFragmentProps(element);
            } else {
              validatePropTypes(element);
            }
            return element;
          }
          var didWarnAboutDeprecatedCreateFactory = false;
          function createFactoryWithValidation(type) {
            var validatedFactory = createElementWithValidation.bind(null, type);
            validatedFactory.type = type;
            {
              if (!didWarnAboutDeprecatedCreateFactory) {
                didWarnAboutDeprecatedCreateFactory = true;
                warn("React.createFactory() is deprecated and will be removed in a future major release. Consider using JSX or use React.createElement() directly instead.");
              }
              Object.defineProperty(validatedFactory, "type", {
                enumerable: false,
                get: function() {
                  warn("Factory.type is deprecated. Access the class directly before passing it to createFactory.");
                  Object.defineProperty(this, "type", {
                    value: type
                  });
                  return type;
                }
              });
            }
            return validatedFactory;
          }
          function cloneElementWithValidation(element, props, children) {
            var newElement = cloneElement.apply(this, arguments);
            for (var i = 2; i < arguments.length; i++) {
              validateChildKeys(arguments[i], newElement.type);
            }
            validatePropTypes(newElement);
            return newElement;
          }
          function startTransition(scope, options) {
            var prevTransition = ReactCurrentBatchConfig.transition;
            ReactCurrentBatchConfig.transition = {};
            var currentTransition = ReactCurrentBatchConfig.transition;
            {
              ReactCurrentBatchConfig.transition._updatedFibers = /* @__PURE__ */ new Set();
            }
            try {
              scope();
            } finally {
              ReactCurrentBatchConfig.transition = prevTransition;
              {
                if (prevTransition === null && currentTransition._updatedFibers) {
                  var updatedFibersCount = currentTransition._updatedFibers.size;
                  if (updatedFibersCount > 10) {
                    warn("Detected a large number of updates inside startTransition. If this is due to a subscription please re-write it to use React provided hooks. Otherwise concurrent mode guarantees are off the table.");
                  }
                  currentTransition._updatedFibers.clear();
                }
              }
            }
          }
          var didWarnAboutMessageChannel = false;
          var enqueueTaskImpl = null;
          function enqueueTask(task) {
            if (enqueueTaskImpl === null) {
              try {
                var requireString = ("require" + Math.random()).slice(0, 7);
                var nodeRequire = module && module[requireString];
                enqueueTaskImpl = nodeRequire.call(module, "timers").setImmediate;
              } catch (_err) {
                enqueueTaskImpl = function(callback) {
                  {
                    if (didWarnAboutMessageChannel === false) {
                      didWarnAboutMessageChannel = true;
                      if (typeof MessageChannel === "undefined") {
                        error("This browser does not have a MessageChannel implementation, so enqueuing tasks via await act(async () => ...) will fail. Please file an issue at https://github.com/facebook/react/issues if you encounter this warning.");
                      }
                    }
                  }
                  var channel = new MessageChannel();
                  channel.port1.onmessage = callback;
                  channel.port2.postMessage(void 0);
                };
              }
            }
            return enqueueTaskImpl(task);
          }
          var actScopeDepth = 0;
          var didWarnNoAwaitAct = false;
          function act(callback) {
            {
              var prevActScopeDepth = actScopeDepth;
              actScopeDepth++;
              if (ReactCurrentActQueue.current === null) {
                ReactCurrentActQueue.current = [];
              }
              var prevIsBatchingLegacy = ReactCurrentActQueue.isBatchingLegacy;
              var result;
              try {
                ReactCurrentActQueue.isBatchingLegacy = true;
                result = callback();
                if (!prevIsBatchingLegacy && ReactCurrentActQueue.didScheduleLegacyUpdate) {
                  var queue = ReactCurrentActQueue.current;
                  if (queue !== null) {
                    ReactCurrentActQueue.didScheduleLegacyUpdate = false;
                    flushActQueue(queue);
                  }
                }
              } catch (error2) {
                popActScope(prevActScopeDepth);
                throw error2;
              } finally {
                ReactCurrentActQueue.isBatchingLegacy = prevIsBatchingLegacy;
              }
              if (result !== null && typeof result === "object" && typeof result.then === "function") {
                var thenableResult = result;
                var wasAwaited = false;
                var thenable = {
                  then: function(resolve, reject) {
                    wasAwaited = true;
                    thenableResult.then(function(returnValue2) {
                      popActScope(prevActScopeDepth);
                      if (actScopeDepth === 0) {
                        recursivelyFlushAsyncActWork(returnValue2, resolve, reject);
                      } else {
                        resolve(returnValue2);
                      }
                    }, function(error2) {
                      popActScope(prevActScopeDepth);
                      reject(error2);
                    });
                  }
                };
                {
                  if (!didWarnNoAwaitAct && typeof Promise !== "undefined") {
                    Promise.resolve().then(function() {
                    }).then(function() {
                      if (!wasAwaited) {
                        didWarnNoAwaitAct = true;
                        error("You called act(async () => ...) without await. This could lead to unexpected testing behaviour, interleaving multiple act calls and mixing their scopes. You should - await act(async () => ...);");
                      }
                    });
                  }
                }
                return thenable;
              } else {
                var returnValue = result;
                popActScope(prevActScopeDepth);
                if (actScopeDepth === 0) {
                  var _queue = ReactCurrentActQueue.current;
                  if (_queue !== null) {
                    flushActQueue(_queue);
                    ReactCurrentActQueue.current = null;
                  }
                  var _thenable = {
                    then: function(resolve, reject) {
                      if (ReactCurrentActQueue.current === null) {
                        ReactCurrentActQueue.current = [];
                        recursivelyFlushAsyncActWork(returnValue, resolve, reject);
                      } else {
                        resolve(returnValue);
                      }
                    }
                  };
                  return _thenable;
                } else {
                  var _thenable2 = {
                    then: function(resolve, reject) {
                      resolve(returnValue);
                    }
                  };
                  return _thenable2;
                }
              }
            }
          }
          function popActScope(prevActScopeDepth) {
            {
              if (prevActScopeDepth !== actScopeDepth - 1) {
                error("You seem to have overlapping act() calls, this is not supported. Be sure to await previous act() calls before making a new one. ");
              }
              actScopeDepth = prevActScopeDepth;
            }
          }
          function recursivelyFlushAsyncActWork(returnValue, resolve, reject) {
            {
              var queue = ReactCurrentActQueue.current;
              if (queue !== null) {
                try {
                  flushActQueue(queue);
                  enqueueTask(function() {
                    if (queue.length === 0) {
                      ReactCurrentActQueue.current = null;
                      resolve(returnValue);
                    } else {
                      recursivelyFlushAsyncActWork(returnValue, resolve, reject);
                    }
                  });
                } catch (error2) {
                  reject(error2);
                }
              } else {
                resolve(returnValue);
              }
            }
          }
          var isFlushing = false;
          function flushActQueue(queue) {
            {
              if (!isFlushing) {
                isFlushing = true;
                var i = 0;
                try {
                  for (; i < queue.length; i++) {
                    var callback = queue[i];
                    do {
                      callback = callback(true);
                    } while (callback !== null);
                  }
                  queue.length = 0;
                } catch (error2) {
                  queue = queue.slice(i + 1);
                  throw error2;
                } finally {
                  isFlushing = false;
                }
              }
            }
          }
          var createElement$1 = createElementWithValidation;
          var cloneElement$1 = cloneElementWithValidation;
          var createFactory = createFactoryWithValidation;
          var Children = {
            map: mapChildren,
            forEach: forEachChildren,
            count: countChildren,
            toArray,
            only: onlyChild
          };
          exports.Children = Children;
          exports.Component = Component;
          exports.Fragment = REACT_FRAGMENT_TYPE;
          exports.Profiler = REACT_PROFILER_TYPE;
          exports.PureComponent = PureComponent;
          exports.StrictMode = REACT_STRICT_MODE_TYPE;
          exports.Suspense = REACT_SUSPENSE_TYPE;
          exports.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = ReactSharedInternals;
          exports.act = act;
          exports.cloneElement = cloneElement$1;
          exports.createContext = createContext;
          exports.createElement = createElement$1;
          exports.createFactory = createFactory;
          exports.createRef = createRef;
          exports.forwardRef = forwardRef;
          exports.isValidElement = isValidElement;
          exports.lazy = lazy;
          exports.memo = memo;
          exports.startTransition = startTransition;
          exports.unstable_act = act;
          exports.useCallback = useCallback;
          exports.useContext = useContext;
          exports.useDebugValue = useDebugValue;
          exports.useDeferredValue = useDeferredValue;
          exports.useEffect = useEffect2;
          exports.useId = useId;
          exports.useImperativeHandle = useImperativeHandle;
          exports.useInsertionEffect = useInsertionEffect;
          exports.useLayoutEffect = useLayoutEffect;
          exports.useMemo = useMemo;
          exports.useReducer = useReducer;
          exports.useRef = useRef;
          exports.useState = useState2;
          exports.useSyncExternalStore = useSyncExternalStore;
          exports.useTransition = useTransition;
          exports.version = ReactVersion;
          if (typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ !== "undefined" && typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.registerInternalModuleStop === "function") {
            __REACT_DEVTOOLS_GLOBAL_HOOK__.registerInternalModuleStop(new Error());
          }
        })();
      }
    }
  });

  // node_modules/react/index.js
  var require_react = __commonJS({
    "node_modules/react/index.js"(exports, module) {
      "use strict";
      if (false) {
        module.exports = null;
      } else {
        module.exports = require_react_development();
      }
    }
  });

  // node_modules/react/cjs/react-jsx-runtime.development.js
  var require_react_jsx_runtime_development = __commonJS({
    "node_modules/react/cjs/react-jsx-runtime.development.js"(exports) {
      "use strict";
      if (true) {
        (function() {
          "use strict";
          var React2 = require_react();
          var REACT_ELEMENT_TYPE = /* @__PURE__ */ Symbol.for("react.element");
          var REACT_PORTAL_TYPE = /* @__PURE__ */ Symbol.for("react.portal");
          var REACT_FRAGMENT_TYPE = /* @__PURE__ */ Symbol.for("react.fragment");
          var REACT_STRICT_MODE_TYPE = /* @__PURE__ */ Symbol.for("react.strict_mode");
          var REACT_PROFILER_TYPE = /* @__PURE__ */ Symbol.for("react.profiler");
          var REACT_PROVIDER_TYPE = /* @__PURE__ */ Symbol.for("react.provider");
          var REACT_CONTEXT_TYPE = /* @__PURE__ */ Symbol.for("react.context");
          var REACT_FORWARD_REF_TYPE = /* @__PURE__ */ Symbol.for("react.forward_ref");
          var REACT_SUSPENSE_TYPE = /* @__PURE__ */ Symbol.for("react.suspense");
          var REACT_SUSPENSE_LIST_TYPE = /* @__PURE__ */ Symbol.for("react.suspense_list");
          var REACT_MEMO_TYPE = /* @__PURE__ */ Symbol.for("react.memo");
          var REACT_LAZY_TYPE = /* @__PURE__ */ Symbol.for("react.lazy");
          var REACT_OFFSCREEN_TYPE = /* @__PURE__ */ Symbol.for("react.offscreen");
          var MAYBE_ITERATOR_SYMBOL = Symbol.iterator;
          var FAUX_ITERATOR_SYMBOL = "@@iterator";
          function getIteratorFn(maybeIterable) {
            if (maybeIterable === null || typeof maybeIterable !== "object") {
              return null;
            }
            var maybeIterator = MAYBE_ITERATOR_SYMBOL && maybeIterable[MAYBE_ITERATOR_SYMBOL] || maybeIterable[FAUX_ITERATOR_SYMBOL];
            if (typeof maybeIterator === "function") {
              return maybeIterator;
            }
            return null;
          }
          var ReactSharedInternals = React2.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED;
          function error(format) {
            {
              {
                for (var _len2 = arguments.length, args = new Array(_len2 > 1 ? _len2 - 1 : 0), _key2 = 1; _key2 < _len2; _key2++) {
                  args[_key2 - 1] = arguments[_key2];
                }
                printWarning("error", format, args);
              }
            }
          }
          function printWarning(level, format, args) {
            {
              var ReactDebugCurrentFrame2 = ReactSharedInternals.ReactDebugCurrentFrame;
              var stack = ReactDebugCurrentFrame2.getStackAddendum();
              if (stack !== "") {
                format += "%s";
                args = args.concat([stack]);
              }
              var argsWithFormat = args.map(function(item) {
                return String(item);
              });
              argsWithFormat.unshift("Warning: " + format);
              Function.prototype.apply.call(console[level], console, argsWithFormat);
            }
          }
          var enableScopeAPI = false;
          var enableCacheElement = false;
          var enableTransitionTracing = false;
          var enableLegacyHidden = false;
          var enableDebugTracing = false;
          var REACT_MODULE_REFERENCE;
          {
            REACT_MODULE_REFERENCE = /* @__PURE__ */ Symbol.for("react.module.reference");
          }
          function isValidElementType(type) {
            if (typeof type === "string" || typeof type === "function") {
              return true;
            }
            if (type === REACT_FRAGMENT_TYPE || type === REACT_PROFILER_TYPE || enableDebugTracing || type === REACT_STRICT_MODE_TYPE || type === REACT_SUSPENSE_TYPE || type === REACT_SUSPENSE_LIST_TYPE || enableLegacyHidden || type === REACT_OFFSCREEN_TYPE || enableScopeAPI || enableCacheElement || enableTransitionTracing) {
              return true;
            }
            if (typeof type === "object" && type !== null) {
              if (type.$$typeof === REACT_LAZY_TYPE || type.$$typeof === REACT_MEMO_TYPE || type.$$typeof === REACT_PROVIDER_TYPE || type.$$typeof === REACT_CONTEXT_TYPE || type.$$typeof === REACT_FORWARD_REF_TYPE || // This needs to include all possible module reference object
              // types supported by any Flight configuration anywhere since
              // we don't know which Flight build this will end up being used
              // with.
              type.$$typeof === REACT_MODULE_REFERENCE || type.getModuleId !== void 0) {
                return true;
              }
            }
            return false;
          }
          function getWrappedName(outerType, innerType, wrapperName) {
            var displayName = outerType.displayName;
            if (displayName) {
              return displayName;
            }
            var functionName = innerType.displayName || innerType.name || "";
            return functionName !== "" ? wrapperName + "(" + functionName + ")" : wrapperName;
          }
          function getContextName(type) {
            return type.displayName || "Context";
          }
          function getComponentNameFromType(type) {
            if (type == null) {
              return null;
            }
            {
              if (typeof type.tag === "number") {
                error("Received an unexpected object in getComponentNameFromType(). This is likely a bug in React. Please file an issue.");
              }
            }
            if (typeof type === "function") {
              return type.displayName || type.name || null;
            }
            if (typeof type === "string") {
              return type;
            }
            switch (type) {
              case REACT_FRAGMENT_TYPE:
                return "Fragment";
              case REACT_PORTAL_TYPE:
                return "Portal";
              case REACT_PROFILER_TYPE:
                return "Profiler";
              case REACT_STRICT_MODE_TYPE:
                return "StrictMode";
              case REACT_SUSPENSE_TYPE:
                return "Suspense";
              case REACT_SUSPENSE_LIST_TYPE:
                return "SuspenseList";
            }
            if (typeof type === "object") {
              switch (type.$$typeof) {
                case REACT_CONTEXT_TYPE:
                  var context = type;
                  return getContextName(context) + ".Consumer";
                case REACT_PROVIDER_TYPE:
                  var provider = type;
                  return getContextName(provider._context) + ".Provider";
                case REACT_FORWARD_REF_TYPE:
                  return getWrappedName(type, type.render, "ForwardRef");
                case REACT_MEMO_TYPE:
                  var outerName = type.displayName || null;
                  if (outerName !== null) {
                    return outerName;
                  }
                  return getComponentNameFromType(type.type) || "Memo";
                case REACT_LAZY_TYPE: {
                  var lazyComponent = type;
                  var payload = lazyComponent._payload;
                  var init = lazyComponent._init;
                  try {
                    return getComponentNameFromType(init(payload));
                  } catch (x) {
                    return null;
                  }
                }
              }
            }
            return null;
          }
          var assign = Object.assign;
          var disabledDepth = 0;
          var prevLog;
          var prevInfo;
          var prevWarn;
          var prevError;
          var prevGroup;
          var prevGroupCollapsed;
          var prevGroupEnd;
          function disabledLog() {
          }
          disabledLog.__reactDisabledLog = true;
          function disableLogs() {
            {
              if (disabledDepth === 0) {
                prevLog = console.log;
                prevInfo = console.info;
                prevWarn = console.warn;
                prevError = console.error;
                prevGroup = console.group;
                prevGroupCollapsed = console.groupCollapsed;
                prevGroupEnd = console.groupEnd;
                var props = {
                  configurable: true,
                  enumerable: true,
                  value: disabledLog,
                  writable: true
                };
                Object.defineProperties(console, {
                  info: props,
                  log: props,
                  warn: props,
                  error: props,
                  group: props,
                  groupCollapsed: props,
                  groupEnd: props
                });
              }
              disabledDepth++;
            }
          }
          function reenableLogs() {
            {
              disabledDepth--;
              if (disabledDepth === 0) {
                var props = {
                  configurable: true,
                  enumerable: true,
                  writable: true
                };
                Object.defineProperties(console, {
                  log: assign({}, props, {
                    value: prevLog
                  }),
                  info: assign({}, props, {
                    value: prevInfo
                  }),
                  warn: assign({}, props, {
                    value: prevWarn
                  }),
                  error: assign({}, props, {
                    value: prevError
                  }),
                  group: assign({}, props, {
                    value: prevGroup
                  }),
                  groupCollapsed: assign({}, props, {
                    value: prevGroupCollapsed
                  }),
                  groupEnd: assign({}, props, {
                    value: prevGroupEnd
                  })
                });
              }
              if (disabledDepth < 0) {
                error("disabledDepth fell below zero. This is a bug in React. Please file an issue.");
              }
            }
          }
          var ReactCurrentDispatcher = ReactSharedInternals.ReactCurrentDispatcher;
          var prefix;
          function describeBuiltInComponentFrame(name, source, ownerFn) {
            {
              if (prefix === void 0) {
                try {
                  throw Error();
                } catch (x) {
                  var match = x.stack.trim().match(/\n( *(at )?)/);
                  prefix = match && match[1] || "";
                }
              }
              return "\n" + prefix + name;
            }
          }
          var reentry = false;
          var componentFrameCache;
          {
            var PossiblyWeakMap = typeof WeakMap === "function" ? WeakMap : Map;
            componentFrameCache = new PossiblyWeakMap();
          }
          function describeNativeComponentFrame(fn, construct) {
            if (!fn || reentry) {
              return "";
            }
            {
              var frame = componentFrameCache.get(fn);
              if (frame !== void 0) {
                return frame;
              }
            }
            var control;
            reentry = true;
            var previousPrepareStackTrace = Error.prepareStackTrace;
            Error.prepareStackTrace = void 0;
            var previousDispatcher;
            {
              previousDispatcher = ReactCurrentDispatcher.current;
              ReactCurrentDispatcher.current = null;
              disableLogs();
            }
            try {
              if (construct) {
                var Fake = function() {
                  throw Error();
                };
                Object.defineProperty(Fake.prototype, "props", {
                  set: function() {
                    throw Error();
                  }
                });
                if (typeof Reflect === "object" && Reflect.construct) {
                  try {
                    Reflect.construct(Fake, []);
                  } catch (x) {
                    control = x;
                  }
                  Reflect.construct(fn, [], Fake);
                } else {
                  try {
                    Fake.call();
                  } catch (x) {
                    control = x;
                  }
                  fn.call(Fake.prototype);
                }
              } else {
                try {
                  throw Error();
                } catch (x) {
                  control = x;
                }
                fn();
              }
            } catch (sample) {
              if (sample && control && typeof sample.stack === "string") {
                var sampleLines = sample.stack.split("\n");
                var controlLines = control.stack.split("\n");
                var s = sampleLines.length - 1;
                var c = controlLines.length - 1;
                while (s >= 1 && c >= 0 && sampleLines[s] !== controlLines[c]) {
                  c--;
                }
                for (; s >= 1 && c >= 0; s--, c--) {
                  if (sampleLines[s] !== controlLines[c]) {
                    if (s !== 1 || c !== 1) {
                      do {
                        s--;
                        c--;
                        if (c < 0 || sampleLines[s] !== controlLines[c]) {
                          var _frame = "\n" + sampleLines[s].replace(" at new ", " at ");
                          if (fn.displayName && _frame.includes("<anonymous>")) {
                            _frame = _frame.replace("<anonymous>", fn.displayName);
                          }
                          {
                            if (typeof fn === "function") {
                              componentFrameCache.set(fn, _frame);
                            }
                          }
                          return _frame;
                        }
                      } while (s >= 1 && c >= 0);
                    }
                    break;
                  }
                }
              }
            } finally {
              reentry = false;
              {
                ReactCurrentDispatcher.current = previousDispatcher;
                reenableLogs();
              }
              Error.prepareStackTrace = previousPrepareStackTrace;
            }
            var name = fn ? fn.displayName || fn.name : "";
            var syntheticFrame = name ? describeBuiltInComponentFrame(name) : "";
            {
              if (typeof fn === "function") {
                componentFrameCache.set(fn, syntheticFrame);
              }
            }
            return syntheticFrame;
          }
          function describeFunctionComponentFrame(fn, source, ownerFn) {
            {
              return describeNativeComponentFrame(fn, false);
            }
          }
          function shouldConstruct(Component) {
            var prototype = Component.prototype;
            return !!(prototype && prototype.isReactComponent);
          }
          function describeUnknownElementTypeFrameInDEV(type, source, ownerFn) {
            if (type == null) {
              return "";
            }
            if (typeof type === "function") {
              {
                return describeNativeComponentFrame(type, shouldConstruct(type));
              }
            }
            if (typeof type === "string") {
              return describeBuiltInComponentFrame(type);
            }
            switch (type) {
              case REACT_SUSPENSE_TYPE:
                return describeBuiltInComponentFrame("Suspense");
              case REACT_SUSPENSE_LIST_TYPE:
                return describeBuiltInComponentFrame("SuspenseList");
            }
            if (typeof type === "object") {
              switch (type.$$typeof) {
                case REACT_FORWARD_REF_TYPE:
                  return describeFunctionComponentFrame(type.render);
                case REACT_MEMO_TYPE:
                  return describeUnknownElementTypeFrameInDEV(type.type, source, ownerFn);
                case REACT_LAZY_TYPE: {
                  var lazyComponent = type;
                  var payload = lazyComponent._payload;
                  var init = lazyComponent._init;
                  try {
                    return describeUnknownElementTypeFrameInDEV(init(payload), source, ownerFn);
                  } catch (x) {
                  }
                }
              }
            }
            return "";
          }
          var hasOwnProperty = Object.prototype.hasOwnProperty;
          var loggedTypeFailures = {};
          var ReactDebugCurrentFrame = ReactSharedInternals.ReactDebugCurrentFrame;
          function setCurrentlyValidatingElement(element) {
            {
              if (element) {
                var owner = element._owner;
                var stack = describeUnknownElementTypeFrameInDEV(element.type, element._source, owner ? owner.type : null);
                ReactDebugCurrentFrame.setExtraStackFrame(stack);
              } else {
                ReactDebugCurrentFrame.setExtraStackFrame(null);
              }
            }
          }
          function checkPropTypes(typeSpecs, values, location, componentName, element) {
            {
              var has = Function.call.bind(hasOwnProperty);
              for (var typeSpecName in typeSpecs) {
                if (has(typeSpecs, typeSpecName)) {
                  var error$1 = void 0;
                  try {
                    if (typeof typeSpecs[typeSpecName] !== "function") {
                      var err = Error((componentName || "React class") + ": " + location + " type `" + typeSpecName + "` is invalid; it must be a function, usually from the `prop-types` package, but received `" + typeof typeSpecs[typeSpecName] + "`.This often happens because of typos such as `PropTypes.function` instead of `PropTypes.func`.");
                      err.name = "Invariant Violation";
                      throw err;
                    }
                    error$1 = typeSpecs[typeSpecName](values, typeSpecName, componentName, location, null, "SECRET_DO_NOT_PASS_THIS_OR_YOU_WILL_BE_FIRED");
                  } catch (ex) {
                    error$1 = ex;
                  }
                  if (error$1 && !(error$1 instanceof Error)) {
                    setCurrentlyValidatingElement(element);
                    error("%s: type specification of %s `%s` is invalid; the type checker function must return `null` or an `Error` but returned a %s. You may have forgotten to pass an argument to the type checker creator (arrayOf, instanceOf, objectOf, oneOf, oneOfType, and shape all require an argument).", componentName || "React class", location, typeSpecName, typeof error$1);
                    setCurrentlyValidatingElement(null);
                  }
                  if (error$1 instanceof Error && !(error$1.message in loggedTypeFailures)) {
                    loggedTypeFailures[error$1.message] = true;
                    setCurrentlyValidatingElement(element);
                    error("Failed %s type: %s", location, error$1.message);
                    setCurrentlyValidatingElement(null);
                  }
                }
              }
            }
          }
          var isArrayImpl = Array.isArray;
          function isArray(a) {
            return isArrayImpl(a);
          }
          function typeName(value) {
            {
              var hasToStringTag = typeof Symbol === "function" && Symbol.toStringTag;
              var type = hasToStringTag && value[Symbol.toStringTag] || value.constructor.name || "Object";
              return type;
            }
          }
          function willCoercionThrow(value) {
            {
              try {
                testStringCoercion(value);
                return false;
              } catch (e) {
                return true;
              }
            }
          }
          function testStringCoercion(value) {
            return "" + value;
          }
          function checkKeyStringCoercion(value) {
            {
              if (willCoercionThrow(value)) {
                error("The provided key is an unsupported type %s. This value must be coerced to a string before before using it here.", typeName(value));
                return testStringCoercion(value);
              }
            }
          }
          var ReactCurrentOwner = ReactSharedInternals.ReactCurrentOwner;
          var RESERVED_PROPS = {
            key: true,
            ref: true,
            __self: true,
            __source: true
          };
          var specialPropKeyWarningShown;
          var specialPropRefWarningShown;
          var didWarnAboutStringRefs;
          {
            didWarnAboutStringRefs = {};
          }
          function hasValidRef(config) {
            {
              if (hasOwnProperty.call(config, "ref")) {
                var getter = Object.getOwnPropertyDescriptor(config, "ref").get;
                if (getter && getter.isReactWarning) {
                  return false;
                }
              }
            }
            return config.ref !== void 0;
          }
          function hasValidKey(config) {
            {
              if (hasOwnProperty.call(config, "key")) {
                var getter = Object.getOwnPropertyDescriptor(config, "key").get;
                if (getter && getter.isReactWarning) {
                  return false;
                }
              }
            }
            return config.key !== void 0;
          }
          function warnIfStringRefCannotBeAutoConverted(config, self) {
            {
              if (typeof config.ref === "string" && ReactCurrentOwner.current && self && ReactCurrentOwner.current.stateNode !== self) {
                var componentName = getComponentNameFromType(ReactCurrentOwner.current.type);
                if (!didWarnAboutStringRefs[componentName]) {
                  error('Component "%s" contains the string ref "%s". Support for string refs will be removed in a future major release. This case cannot be automatically converted to an arrow function. We ask you to manually fix this case by using useRef() or createRef() instead. Learn more about using refs safely here: https://reactjs.org/link/strict-mode-string-ref', getComponentNameFromType(ReactCurrentOwner.current.type), config.ref);
                  didWarnAboutStringRefs[componentName] = true;
                }
              }
            }
          }
          function defineKeyPropWarningGetter(props, displayName) {
            {
              var warnAboutAccessingKey = function() {
                if (!specialPropKeyWarningShown) {
                  specialPropKeyWarningShown = true;
                  error("%s: `key` is not a prop. Trying to access it will result in `undefined` being returned. If you need to access the same value within the child component, you should pass it as a different prop. (https://reactjs.org/link/special-props)", displayName);
                }
              };
              warnAboutAccessingKey.isReactWarning = true;
              Object.defineProperty(props, "key", {
                get: warnAboutAccessingKey,
                configurable: true
              });
            }
          }
          function defineRefPropWarningGetter(props, displayName) {
            {
              var warnAboutAccessingRef = function() {
                if (!specialPropRefWarningShown) {
                  specialPropRefWarningShown = true;
                  error("%s: `ref` is not a prop. Trying to access it will result in `undefined` being returned. If you need to access the same value within the child component, you should pass it as a different prop. (https://reactjs.org/link/special-props)", displayName);
                }
              };
              warnAboutAccessingRef.isReactWarning = true;
              Object.defineProperty(props, "ref", {
                get: warnAboutAccessingRef,
                configurable: true
              });
            }
          }
          var ReactElement = function(type, key, ref, self, source, owner, props) {
            var element = {
              // This tag allows us to uniquely identify this as a React Element
              $$typeof: REACT_ELEMENT_TYPE,
              // Built-in properties that belong on the element
              type,
              key,
              ref,
              props,
              // Record the component responsible for creating this element.
              _owner: owner
            };
            {
              element._store = {};
              Object.defineProperty(element._store, "validated", {
                configurable: false,
                enumerable: false,
                writable: true,
                value: false
              });
              Object.defineProperty(element, "_self", {
                configurable: false,
                enumerable: false,
                writable: false,
                value: self
              });
              Object.defineProperty(element, "_source", {
                configurable: false,
                enumerable: false,
                writable: false,
                value: source
              });
              if (Object.freeze) {
                Object.freeze(element.props);
                Object.freeze(element);
              }
            }
            return element;
          };
          function jsxDEV(type, config, maybeKey, source, self) {
            {
              var propName;
              var props = {};
              var key = null;
              var ref = null;
              if (maybeKey !== void 0) {
                {
                  checkKeyStringCoercion(maybeKey);
                }
                key = "" + maybeKey;
              }
              if (hasValidKey(config)) {
                {
                  checkKeyStringCoercion(config.key);
                }
                key = "" + config.key;
              }
              if (hasValidRef(config)) {
                ref = config.ref;
                warnIfStringRefCannotBeAutoConverted(config, self);
              }
              for (propName in config) {
                if (hasOwnProperty.call(config, propName) && !RESERVED_PROPS.hasOwnProperty(propName)) {
                  props[propName] = config[propName];
                }
              }
              if (type && type.defaultProps) {
                var defaultProps = type.defaultProps;
                for (propName in defaultProps) {
                  if (props[propName] === void 0) {
                    props[propName] = defaultProps[propName];
                  }
                }
              }
              if (key || ref) {
                var displayName = typeof type === "function" ? type.displayName || type.name || "Unknown" : type;
                if (key) {
                  defineKeyPropWarningGetter(props, displayName);
                }
                if (ref) {
                  defineRefPropWarningGetter(props, displayName);
                }
              }
              return ReactElement(type, key, ref, self, source, ReactCurrentOwner.current, props);
            }
          }
          var ReactCurrentOwner$1 = ReactSharedInternals.ReactCurrentOwner;
          var ReactDebugCurrentFrame$1 = ReactSharedInternals.ReactDebugCurrentFrame;
          function setCurrentlyValidatingElement$1(element) {
            {
              if (element) {
                var owner = element._owner;
                var stack = describeUnknownElementTypeFrameInDEV(element.type, element._source, owner ? owner.type : null);
                ReactDebugCurrentFrame$1.setExtraStackFrame(stack);
              } else {
                ReactDebugCurrentFrame$1.setExtraStackFrame(null);
              }
            }
          }
          var propTypesMisspellWarningShown;
          {
            propTypesMisspellWarningShown = false;
          }
          function isValidElement(object) {
            {
              return typeof object === "object" && object !== null && object.$$typeof === REACT_ELEMENT_TYPE;
            }
          }
          function getDeclarationErrorAddendum() {
            {
              if (ReactCurrentOwner$1.current) {
                var name = getComponentNameFromType(ReactCurrentOwner$1.current.type);
                if (name) {
                  return "\n\nCheck the render method of `" + name + "`.";
                }
              }
              return "";
            }
          }
          function getSourceInfoErrorAddendum(source) {
            {
              if (source !== void 0) {
                var fileName = source.fileName.replace(/^.*[\\\/]/, "");
                var lineNumber = source.lineNumber;
                return "\n\nCheck your code at " + fileName + ":" + lineNumber + ".";
              }
              return "";
            }
          }
          var ownerHasKeyUseWarning = {};
          function getCurrentComponentErrorInfo(parentType) {
            {
              var info = getDeclarationErrorAddendum();
              if (!info) {
                var parentName = typeof parentType === "string" ? parentType : parentType.displayName || parentType.name;
                if (parentName) {
                  info = "\n\nCheck the top-level render call using <" + parentName + ">.";
                }
              }
              return info;
            }
          }
          function validateExplicitKey(element, parentType) {
            {
              if (!element._store || element._store.validated || element.key != null) {
                return;
              }
              element._store.validated = true;
              var currentComponentErrorInfo = getCurrentComponentErrorInfo(parentType);
              if (ownerHasKeyUseWarning[currentComponentErrorInfo]) {
                return;
              }
              ownerHasKeyUseWarning[currentComponentErrorInfo] = true;
              var childOwner = "";
              if (element && element._owner && element._owner !== ReactCurrentOwner$1.current) {
                childOwner = " It was passed a child from " + getComponentNameFromType(element._owner.type) + ".";
              }
              setCurrentlyValidatingElement$1(element);
              error('Each child in a list should have a unique "key" prop.%s%s See https://reactjs.org/link/warning-keys for more information.', currentComponentErrorInfo, childOwner);
              setCurrentlyValidatingElement$1(null);
            }
          }
          function validateChildKeys(node, parentType) {
            {
              if (typeof node !== "object") {
                return;
              }
              if (isArray(node)) {
                for (var i = 0; i < node.length; i++) {
                  var child = node[i];
                  if (isValidElement(child)) {
                    validateExplicitKey(child, parentType);
                  }
                }
              } else if (isValidElement(node)) {
                if (node._store) {
                  node._store.validated = true;
                }
              } else if (node) {
                var iteratorFn = getIteratorFn(node);
                if (typeof iteratorFn === "function") {
                  if (iteratorFn !== node.entries) {
                    var iterator = iteratorFn.call(node);
                    var step;
                    while (!(step = iterator.next()).done) {
                      if (isValidElement(step.value)) {
                        validateExplicitKey(step.value, parentType);
                      }
                    }
                  }
                }
              }
            }
          }
          function validatePropTypes(element) {
            {
              var type = element.type;
              if (type === null || type === void 0 || typeof type === "string") {
                return;
              }
              var propTypes;
              if (typeof type === "function") {
                propTypes = type.propTypes;
              } else if (typeof type === "object" && (type.$$typeof === REACT_FORWARD_REF_TYPE || // Note: Memo only checks outer props here.
              // Inner props are checked in the reconciler.
              type.$$typeof === REACT_MEMO_TYPE)) {
                propTypes = type.propTypes;
              } else {
                return;
              }
              if (propTypes) {
                var name = getComponentNameFromType(type);
                checkPropTypes(propTypes, element.props, "prop", name, element);
              } else if (type.PropTypes !== void 0 && !propTypesMisspellWarningShown) {
                propTypesMisspellWarningShown = true;
                var _name = getComponentNameFromType(type);
                error("Component %s declared `PropTypes` instead of `propTypes`. Did you misspell the property assignment?", _name || "Unknown");
              }
              if (typeof type.getDefaultProps === "function" && !type.getDefaultProps.isReactClassApproved) {
                error("getDefaultProps is only used on classic React.createClass definitions. Use a static property named `defaultProps` instead.");
              }
            }
          }
          function validateFragmentProps(fragment) {
            {
              var keys = Object.keys(fragment.props);
              for (var i = 0; i < keys.length; i++) {
                var key = keys[i];
                if (key !== "children" && key !== "key") {
                  setCurrentlyValidatingElement$1(fragment);
                  error("Invalid prop `%s` supplied to `React.Fragment`. React.Fragment can only have `key` and `children` props.", key);
                  setCurrentlyValidatingElement$1(null);
                  break;
                }
              }
              if (fragment.ref !== null) {
                setCurrentlyValidatingElement$1(fragment);
                error("Invalid attribute `ref` supplied to `React.Fragment`.");
                setCurrentlyValidatingElement$1(null);
              }
            }
          }
          var didWarnAboutKeySpread = {};
          function jsxWithValidation(type, props, key, isStaticChildren, source, self) {
            {
              var validType = isValidElementType(type);
              if (!validType) {
                var info = "";
                if (type === void 0 || typeof type === "object" && type !== null && Object.keys(type).length === 0) {
                  info += " You likely forgot to export your component from the file it's defined in, or you might have mixed up default and named imports.";
                }
                var sourceInfo = getSourceInfoErrorAddendum(source);
                if (sourceInfo) {
                  info += sourceInfo;
                } else {
                  info += getDeclarationErrorAddendum();
                }
                var typeString;
                if (type === null) {
                  typeString = "null";
                } else if (isArray(type)) {
                  typeString = "array";
                } else if (type !== void 0 && type.$$typeof === REACT_ELEMENT_TYPE) {
                  typeString = "<" + (getComponentNameFromType(type.type) || "Unknown") + " />";
                  info = " Did you accidentally export a JSX literal instead of a component?";
                } else {
                  typeString = typeof type;
                }
                error("React.jsx: type is invalid -- expected a string (for built-in components) or a class/function (for composite components) but got: %s.%s", typeString, info);
              }
              var element = jsxDEV(type, props, key, source, self);
              if (element == null) {
                return element;
              }
              if (validType) {
                var children = props.children;
                if (children !== void 0) {
                  if (isStaticChildren) {
                    if (isArray(children)) {
                      for (var i = 0; i < children.length; i++) {
                        validateChildKeys(children[i], type);
                      }
                      if (Object.freeze) {
                        Object.freeze(children);
                      }
                    } else {
                      error("React.jsx: Static children should always be an array. You are likely explicitly calling React.jsxs or React.jsxDEV. Use the Babel transform instead.");
                    }
                  } else {
                    validateChildKeys(children, type);
                  }
                }
              }
              {
                if (hasOwnProperty.call(props, "key")) {
                  var componentName = getComponentNameFromType(type);
                  var keys = Object.keys(props).filter(function(k) {
                    return k !== "key";
                  });
                  var beforeExample = keys.length > 0 ? "{key: someKey, " + keys.join(": ..., ") + ": ...}" : "{key: someKey}";
                  if (!didWarnAboutKeySpread[componentName + beforeExample]) {
                    var afterExample = keys.length > 0 ? "{" + keys.join(": ..., ") + ": ...}" : "{}";
                    error('A props object containing a "key" prop is being spread into JSX:\n  let props = %s;\n  <%s {...props} />\nReact keys must be passed directly to JSX without using spread:\n  let props = %s;\n  <%s key={someKey} {...props} />', beforeExample, componentName, afterExample, componentName);
                    didWarnAboutKeySpread[componentName + beforeExample] = true;
                  }
                }
              }
              if (type === REACT_FRAGMENT_TYPE) {
                validateFragmentProps(element);
              } else {
                validatePropTypes(element);
              }
              return element;
            }
          }
          function jsxWithValidationStatic(type, props, key) {
            {
              return jsxWithValidation(type, props, key, true);
            }
          }
          function jsxWithValidationDynamic(type, props, key) {
            {
              return jsxWithValidation(type, props, key, false);
            }
          }
          var jsx2 = jsxWithValidationDynamic;
          var jsxs2 = jsxWithValidationStatic;
          exports.Fragment = REACT_FRAGMENT_TYPE;
          exports.jsx = jsx2;
          exports.jsxs = jsxs2;
        })();
      }
    }
  });

  // node_modules/react/jsx-runtime.js
  var require_jsx_runtime = __commonJS({
    "node_modules/react/jsx-runtime.js"(exports, module) {
      "use strict";
      if (false) {
        module.exports = null;
      } else {
        module.exports = require_react_jsx_runtime_development();
      }
    }
  });

  // src/App.tsx
  var import_react = __toESM(require_react(), 1);

  // src/lib/api.ts
  var API_BASE = "https://codestreak-api.onrender.com/api";
  async function checkExtensionVersion() {
    try {
      const res = await fetch(`${API_BASE}/extension/version`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }
  async function getAppConfig() {
    try {
      const res = await fetch(`${API_BASE}/config/app`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }
  async function request(path, options) {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Request failed (${res.status})`);
    }
    return res.json();
  }
  var api = {
    register: (name, leetcode_username, email, password) => request("/users/register", {
      method: "POST",
      body: JSON.stringify({ name, leetcode_username, email, password })
    }),
    login: (leetcode_username, password) => request("/users/login", {
      method: "POST",
      body: JSON.stringify({ leetcode_username, password })
    }),
    initiateForgotPassword: (email_or_username) => request("/users/forgot-password/initiate", {
      method: "POST",
      body: JSON.stringify({ email_or_username })
    }),
    verifyForgotPassword: (email_or_username, otp, new_password) => request("/users/forgot-password/verify", {
      method: "POST",
      body: JSON.stringify({ email_or_username, otp, new_password })
    }),
    dashboard: (userId) => request(`/users/${userId}/dashboard`),
    syncUser: (userId) => request(`/users/${userId}/sync`, { method: "POST" }),
    updateLeetcodeUsername: (userId, leetcode_username) => request(
      `/users/${userId}/leetcode-username`,
      {
        method: "PUT",
        body: JSON.stringify({ leetcode_username })
      }
    ),
    deleteAccount: (userId, password) => request(`/users/${userId}/delete-account`, {
      method: "POST",
      body: JSON.stringify({ password })
    }),
    leaderboard: (userId, sortBy = "points") => {
      const params = new URLSearchParams();
      if (userId) params.set("user_id", String(userId));
      if (sortBy) params.set("sort_by", sortBy);
      return request(`/leaderboard?${params.toString()}`);
    },
    friendsLeaderboard: (userId, sortBy = "points") => {
      const params = new URLSearchParams();
      params.set("user_id", String(userId));
      if (sortBy) params.set("sort_by", sortBy);
      return request(`/friends/leaderboard?${params.toString()}`);
    },
    createGroup: (userId, name) => request("/groups", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, name })
    }),
    joinGroup: (userId, code) => request("/groups/join", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, code })
    }),
    removeMember: (groupId, memberUserId, requesterUserId) => request(
      `/groups/${groupId}/members/${memberUserId}?requester_id=${requesterUserId}`,
      { method: "DELETE" }
    ),
    myGroups: (userId) => request(`/groups/my-groups/${userId}`),
    groupLeaderboard: (groupId, userId, sortBy = "points") => {
      const params = new URLSearchParams();
      if (userId) params.set("user_id", String(userId));
      if (sortBy) params.set("sort_by", sortBy);
      return request(`/groups/${groupId}/leaderboard?${params.toString()}`);
    },
    toggleKudos: (toUserId, fromUserId) => request(
      `/kudos/${toUserId}`,
      {
        method: "POST",
        body: JSON.stringify({ from_user_id: fromUserId })
      }
    ),
    recentSolves: (userId, limit = 10) => request(`/users/${userId}/recent-solves?limit=${limit}`),
    pollNow: () => request("/admin/poll-now", { method: "POST" }),
    checkExtensionVersion,
    getAppConfig
  };

  // src/storage.ts
  var hasChromeStorage = typeof chrome !== "undefined" && !!chrome.storage?.local;
  async function getStored(key) {
    if (hasChromeStorage) {
      return new Promise((resolve) => {
        chrome.storage.local.get([key], (result) => resolve(result[key] ?? null));
      });
    }
    return localStorage.getItem(key);
  }
  async function setStored(key, value) {
    if (hasChromeStorage) {
      return new Promise((resolve) => {
        chrome.storage.local.set({ [key]: value }, () => resolve());
      });
    }
    localStorage.setItem(key, value);
  }
  async function clearStored(keys) {
    if (hasChromeStorage) {
      return new Promise((resolve) => {
        chrome.storage.local.remove(keys, () => resolve());
      });
    }
    keys.forEach((k) => localStorage.removeItem(k));
  }

  // src/App.tsx
  var import_jsx_runtime = __toESM(require_jsx_runtime(), 1);
  function App() {
    const [view, setView] = (0, import_react.useState)("loading");
    const [userId, setUserId] = (0, import_react.useState)(null);
    const [error, setError] = (0, import_react.useState)(null);
    const [showPointsHelp, setShowPointsHelp] = (0, import_react.useState)(false);
    (0, import_react.useEffect)(() => {
      (async () => {
        const stored = await getStored("codestreak_user_id");
        if (stored) {
          setUserId(Number(stored));
          setView("dashboard");
        } else {
          setView("onboarding");
        }
      })();
    }, []);
    async function handleRegistered(id) {
      await setStored("codestreak_user_id", String(id));
      setUserId(id);
      setView("dashboard");
    }
    async function handleLogout() {
      await clearStored(["codestreak_user_id"]);
      setUserId(null);
      setView("onboarding");
    }
    return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "app", children: [
      /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("header", { className: "header", children: [
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "logo-group", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("img", { src: "/icon48.png", alt: "LeetStreak", className: "header-logo-img" }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "logo-text", children: "LeetStreak" })
        ] }),
        view === "dashboard" && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "header-actions", children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
          "button",
          {
            className: "help-btn",
            onClick: () => setShowPointsHelp(true),
            title: "How Points Work \u2753",
            children: "\u2753 Help"
          }
        ) })
      ] }),
      showPointsHelp && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(PointsHelpModal, { onClose: () => setShowPointsHelp(false) }),
      view === "loading" && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "centered muted", children: "Loading profile\u2026" }),
      view === "onboarding" && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Onboarding, { onRegistered: handleRegistered, onError: setError }),
      view === "dashboard" && userId && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Dashboard, { userId, onResetUser: handleLogout }),
      error && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "error-banner", children: error })
    ] });
  }
  function Onboarding({
    onRegistered,
    onError
  }) {
    const [authMode, setAuthMode] = (0, import_react.useState)("login");
    const [name, setName] = (0, import_react.useState)("");
    const [username, setUsername] = (0, import_react.useState)("");
    const [email, setEmail] = (0, import_react.useState)("");
    const [password, setPassword] = (0, import_react.useState)("");
    const [newPassword, setNewPassword] = (0, import_react.useState)("");
    const [otp, setOtp] = (0, import_react.useState)("");
    const [forgotStep, setForgotStep] = (0, import_react.useState)(1);
    const [sentEmail, setSentEmail] = (0, import_react.useState)("");
    const [busy, setBusy] = (0, import_react.useState)(false);
    const [successMsg, setSuccessMsg] = (0, import_react.useState)(null);
    const [draftsLoaded, setDraftsLoaded] = (0, import_react.useState)(false);
    const AUTH_STORAGE_KEYS = [
      "codestreak_auth_mode",
      "codestreak_forgot_step",
      "codestreak_sent_email",
      "codestreak_draft_name",
      "codestreak_draft_username",
      "codestreak_draft_email",
      "codestreak_draft_password",
      "codestreak_draft_new_password",
      "codestreak_draft_otp"
    ];
    (0, import_react.useEffect)(() => {
      (async () => {
        const storedMode = await getStored("codestreak_auth_mode");
        const storedStep = await getStored("codestreak_forgot_step");
        const storedEmail = await getStored("codestreak_sent_email");
        const draftName = await getStored("codestreak_draft_name");
        const draftUsername = await getStored("codestreak_draft_username");
        const draftEmail = await getStored("codestreak_draft_email");
        const draftPassword = await getStored("codestreak_draft_password");
        const draftNewPassword = await getStored("codestreak_draft_new_password");
        const draftOtp = await getStored("codestreak_draft_otp");
        if (draftName) setName(draftName);
        if (draftUsername) setUsername(draftUsername);
        if (draftEmail) setEmail(draftEmail);
        if (draftPassword) setPassword(draftPassword);
        if (draftNewPassword) setNewPassword(draftNewPassword);
        if (draftOtp) setOtp(draftOtp);
        if (storedMode === "forgot" && storedStep === "2" && storedEmail) {
          setAuthMode("forgot");
          setForgotStep(2);
          setSentEmail(storedEmail);
          if (!draftUsername) setUsername(storedEmail);
        } else if (storedMode === "login" || storedMode === "register" || storedMode === "forgot") {
          setAuthMode(storedMode);
        }
        setDraftsLoaded(true);
      })();
    }, []);
    (0, import_react.useEffect)(() => {
      if (draftsLoaded) setStored("codestreak_draft_name", name);
    }, [name, draftsLoaded]);
    (0, import_react.useEffect)(() => {
      if (draftsLoaded) setStored("codestreak_draft_username", username);
    }, [username, draftsLoaded]);
    (0, import_react.useEffect)(() => {
      if (draftsLoaded) setStored("codestreak_draft_email", email);
    }, [email, draftsLoaded]);
    (0, import_react.useEffect)(() => {
      if (draftsLoaded) setStored("codestreak_draft_password", password);
    }, [password, draftsLoaded]);
    (0, import_react.useEffect)(() => {
      if (draftsLoaded) setStored("codestreak_draft_new_password", newPassword);
    }, [newPassword, draftsLoaded]);
    (0, import_react.useEffect)(() => {
      if (draftsLoaded) setStored("codestreak_draft_otp", otp);
    }, [otp, draftsLoaded]);
    const switchAuthMode = async (mode) => {
      setAuthMode(mode);
      onError(null);
      setSuccessMsg(null);
      await setStored("codestreak_auth_mode", mode);
    };
    async function handleLogin(e) {
      e.preventDefault();
      if (!username.trim() || !password) return;
      setBusy(true);
      onError(null);
      try {
        const res = await api.login(username.trim(), password);
        await clearStored(AUTH_STORAGE_KEYS);
        onRegistered(res.id);
      } catch (err) {
        onError(err instanceof Error ? err.message : "Login failed.");
      } finally {
        setBusy(false);
      }
    }
    async function handleRegister(e) {
      e.preventDefault();
      if (!name.trim() || !username.trim() || !email.trim() || !password) return;
      setBusy(true);
      onError(null);
      try {
        const res = await api.register(name.trim(), username.trim(), email.trim(), password);
        await clearStored(AUTH_STORAGE_KEYS);
        onRegistered(res.id);
      } catch (err) {
        onError(err instanceof Error ? err.message : "Registration failed.");
      } finally {
        setBusy(false);
      }
    }
    async function handleForgotInitiate(e) {
      e.preventDefault();
      if (!username.trim()) return;
      setBusy(true);
      onError(null);
      try {
        const res = await api.initiateForgotPassword(username.trim());
        setSentEmail(res.email);
        setForgotStep(2);
        setSuccessMsg(`Sent 6-digit code to ${res.email}`);
        await setStored("codestreak_auth_mode", "forgot");
        await setStored("codestreak_forgot_step", "2");
        await setStored("codestreak_sent_email", res.email);
      } catch (err) {
        onError(err instanceof Error ? err.message : "Could not send reset code.");
      } finally {
        setBusy(false);
      }
    }
    async function handleForgotVerify(e) {
      e.preventDefault();
      if (!username.trim() || !otp.trim() || !newPassword) return;
      setBusy(true);
      onError(null);
      try {
        await api.verifyForgotPassword(username.trim(), otp.trim(), newPassword);
        setPassword(newPassword);
        const res = await api.login(username.trim(), newPassword);
        await clearStored(AUTH_STORAGE_KEYS);
        onRegistered(res.id);
      } catch (err) {
        onError(err instanceof Error ? err.message : "Verification failed.");
      } finally {
        setBusy(false);
      }
    }
    return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "onboarding", children: [
      /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "onboarding-welcome", children: [
        /* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", { children: "Welcome to LeetStreak" }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { className: "muted small", children: "Track LeetCode consistency with friends, form private groups, and build your daily streak." })
      ] }),
      successMsg && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "sync-banner", children: successMsg }),
      /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "auth-card", children: [
        authMode !== "forgot" && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "auth-tab-bar", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
            "button",
            {
              type: "button",
              className: `auth-tab-btn ${authMode === "login" ? "active" : ""}`,
              onClick: () => switchAuthMode("login"),
              children: "Log In"
            }
          ),
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
            "button",
            {
              type: "button",
              className: `auth-tab-btn ${authMode === "register" ? "active" : ""}`,
              onClick: () => switchAuthMode("register"),
              children: "Sign Up"
            }
          )
        ] }),
        authMode === "login" && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", { onSubmit: handleLogin, className: "auth-form", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", { children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "Email" }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
              "input",
              {
                type: "email",
                value: username,
                onChange: (e) => setUsername(e.target.value),
                placeholder: "e.g. alex@example.com",
                required: true
              }
            )
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", { children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "Password" }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
              "input",
              {
                type: "password",
                value: password,
                onChange: (e) => setPassword(e.target.value),
                placeholder: "\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022",
                required: true
              }
            )
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", { type: "submit", className: "primary-btn", disabled: busy, children: busy ? "Verifying\u2026" : "Log In" }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "auth-footer-links", children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
            "button",
            {
              type: "button",
              className: "link-btn tiny",
              onClick: () => {
                switchAuthMode("forgot");
                setForgotStep(1);
              },
              children: "Forgot Password?"
            }
          ) })
        ] }),
        authMode === "register" && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", { onSubmit: handleRegister, className: "auth-form", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", { children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "Your Name" }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
              "input",
              {
                value: name,
                onChange: (e) => setName(e.target.value),
                placeholder: "e.g. Alex",
                required: true
              }
            )
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", { children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "LeetCode Username" }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
              "input",
              {
                value: username,
                onChange: (e) => setUsername(e.target.value),
                placeholder: "e.g. neal_wu",
                required: true
              }
            )
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", { children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "Email Address" }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
              "input",
              {
                type: "email",
                value: email,
                onChange: (e) => setEmail(e.target.value),
                placeholder: "alex@example.com",
                required: true
              }
            )
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", { children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "Password" }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
              "input",
              {
                type: "password",
                value: password,
                onChange: (e) => setPassword(e.target.value),
                placeholder: "At least 4 characters",
                required: true
              }
            )
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", { type: "submit", className: "primary-btn", disabled: busy, children: busy ? "Creating Account\u2026" : "Create Account" })
        ] }),
        authMode === "forgot" && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "auth-form", children: forgotStep === 1 ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", { onSubmit: handleForgotInitiate, className: "auth-form", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { className: "tiny muted mb-1", children: "Enter your Email address to receive a 6-digit reset code." }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", { children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "Email Address" }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
              "input",
              {
                type: "email",
                value: username,
                onChange: (e) => setUsername(e.target.value),
                placeholder: "e.g. alex@example.com",
                required: true
              }
            )
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", { type: "submit", className: "primary-btn", disabled: busy, children: busy ? "Sending Code\u2026" : "Send Reset Code" }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "auth-footer-links", children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
            "button",
            {
              type: "button",
              className: "link-btn tiny",
              onClick: () => switchAuthMode("login"),
              children: "\u2190 Back to Log In"
            }
          ) })
        ] }) : /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", { onSubmit: handleForgotVerify, className: "auth-form", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", { className: "tiny muted mb-1", children: [
            "Enter the 6-digit code sent to ",
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("strong", { children: sentEmail }),
            " and your new password."
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", { children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "6-Digit Verification Code" }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
              "input",
              {
                value: otp,
                onChange: (e) => setOtp(e.target.value),
                placeholder: "e.g. 839102",
                maxLength: 6,
                required: true
              }
            )
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", { children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "New Password" }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
              "input",
              {
                type: "password",
                value: newPassword,
                onChange: (e) => setNewPassword(e.target.value),
                placeholder: "New password",
                required: true
              }
            )
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", { type: "submit", className: "primary-btn", disabled: busy, children: busy ? "Resetting\u2026" : "Reset & Log In" }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "auth-footer-links", style: { display: "flex", justifyContent: "space-between", width: "100%" }, children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
              "button",
              {
                type: "button",
                className: "link-btn tiny",
                onClick: () => switchAuthMode("login"),
                children: "\u2190 Back to Log In"
              }
            ),
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
              "button",
              {
                type: "button",
                className: "link-btn tiny",
                onClick: () => setForgotStep(1),
                children: "Resend Code"
              }
            )
          ] })
        ] }) })
      ] })
    ] });
  }
  function Dashboard({
    userId,
    onResetUser
  }) {
    const [dash, setDash] = (0, import_react.useState)(null);
    const [board, setBoard] = (0, import_react.useState)(null);
    const [groups, setGroups] = (0, import_react.useState)([]);
    const [selectedTab, setSelectedTab] = (0, import_react.useState)("global");
    const [sortBy, setSortBy] = (0, import_react.useState)("points");
    const [revealedCodes, setRevealedCodes] = (0, import_react.useState)({});
    const [activityFeed, setActivityFeed] = (0, import_react.useState)([]);
    const [tabBoards, setTabBoards] = (0, import_react.useState)({});
    const [boardLoading, setBoardLoading] = (0, import_react.useState)(false);
    const changeTab = (tab) => {
      const tabKey = String(tab);
      setSelectedTab(tab);
      setStored("codestreak_active_tab", tabKey);
      if (tabBoards[tabKey]) {
        setBoard(tabBoards[tabKey]);
        setBoardLoading(false);
      } else {
        setBoard(null);
        setBoardLoading(true);
      }
    };
    (0, import_react.useEffect)(() => {
      (async () => {
        const storedTab = await getStored("codestreak_active_tab");
        let activeTabKey = "global";
        if (storedTab) {
          if (storedTab === "global" || storedTab === "friends") {
            setSelectedTab(storedTab);
            activeTabKey = storedTab;
          } else if (!isNaN(Number(storedTab))) {
            setSelectedTab(Number(storedTab));
            activeTabKey = storedTab;
          }
        }
        const cachedDash = await getStored("codestreak_cached_dash");
        const cachedBoard = await getStored(`codestreak_cached_board_${activeTabKey}`) || await getStored("codestreak_cached_board");
        if (cachedDash) {
          try {
            setDash(JSON.parse(cachedDash));
          } catch (e) {
          }
        }
        if (cachedBoard) {
          try {
            const parsed = JSON.parse(cachedBoard);
            setBoard(parsed);
            setTabBoards((prev) => ({ ...prev, [activeTabKey]: parsed }));
          } catch (e) {
          }
        }
      })();
    }, []);
    const [inspectedFriend, setInspectedFriend] = (0, import_react.useState)(
      null
    );
    const [friendDash, setFriendDash] = (0, import_react.useState)(null);
    const [loadingFriendDash, setLoadingFriendDash] = (0, import_react.useState)(false);
    const [modalTab, setModalTab] = (0, import_react.useState)("overview");
    const [recentSolvesList, setRecentSolvesList] = (0, import_react.useState)([]);
    const [loadingRecentSolves, setLoadingRecentSolves] = (0, import_react.useState)(false);
    const [avatarLoadError, setAvatarLoadError] = (0, import_react.useState)(false);
    const [syncing, setSyncing] = (0, import_react.useState)(false);
    const [syncMsg, setSyncMsg] = (0, import_react.useState)(null);
    const [error, setError] = (0, import_react.useState)(null);
    const [toastSolve, setToastSolve] = (0, import_react.useState)(null);
    const [showSettings, setShowSettings] = (0, import_react.useState)(false);
    const [showCoffeeModal, setShowCoffeeModal] = (0, import_react.useState)(false);
    const [newLeetcodeUsername, setNewLeetcodeUsername] = (0, import_react.useState)("");
    const [updatingUsername, setUpdatingUsername] = (0, import_react.useState)(false);
    const [settingsMsg, setSettingsMsg] = (0, import_react.useState)(null);
    const [showDeleteModal, setShowDeleteModal] = (0, import_react.useState)(false);
    const [deletePassword, setDeletePassword] = (0, import_react.useState)("");
    const [deletingAccount, setDeletingAccount] = (0, import_react.useState)(false);
    const [deleteError, setDeleteError] = (0, import_react.useState)(null);
    const [showCreateGroup, setShowCreateGroup] = (0, import_react.useState)(false);
    const [showJoinGroup, setShowJoinGroup] = (0, import_react.useState)(false);
    const [newGroupName, setNewGroupName] = (0, import_react.useState)("");
    const [joinCode, setJoinCode] = (0, import_react.useState)("");
    const [groupActionBusy, setGroupActionBusy] = (0, import_react.useState)(false);
    const [copiedCode, setCopiedCode] = (0, import_react.useState)(false);
    const [shareMsg, setShareMsg] = (0, import_react.useState)(null);
    const [showPointsHelp, setShowPointsHelp] = (0, import_react.useState)(false);
    const [isOffline, setIsOffline] = (0, import_react.useState)(!navigator.onLine);
    const [appConfig, setAppConfig] = (0, import_react.useState)(null);
    (0, import_react.useEffect)(() => {
      const handleOnline = () => setIsOffline(false);
      const handleOffline = () => setIsOffline(true);
      window.addEventListener("online", handleOnline);
      window.addEventListener("offline", handleOffline);
      api.getAppConfig().then((cfg) => {
        if (cfg) setAppConfig(cfg);
      });
      return () => {
        window.removeEventListener("online", handleOnline);
        window.removeEventListener("offline", handleOffline);
      };
    }, []);
    function handleShareGroup(groupName, code) {
      const inviteText = `Join my LeetStreak group "${groupName}"! Use Invite Code: ${code}`;
      navigator.clipboard.writeText(inviteText);
      setShareMsg("Copied Invite!");
      setTimeout(() => setShareMsg(null), 2500);
    }
    async function handleUpdateUsername(e) {
      e.preventDefault();
      if (!newLeetcodeUsername.trim()) return;
      setUpdatingUsername(true);
      setSettingsMsg(null);
      setError(null);
      try {
        const res = await api.updateLeetcodeUsername(userId, newLeetcodeUsername.trim());
        setSettingsMsg(`Updated username to @${res.leetcode_username}!`);
        await loadData(selectedTab);
        setTimeout(() => {
          setShowSettings(false);
          setSettingsMsg(null);
        }, 1500);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to update username.");
      } finally {
        setUpdatingUsername(false);
      }
    }
    async function handleDeleteAccount(e) {
      e.preventDefault();
      if (!deletePassword) return;
      setDeletingAccount(true);
      setDeleteError(null);
      try {
        await api.deleteAccount(userId, deletePassword);
        setShowDeleteModal(false);
        setShowSettings(false);
        onResetUser();
      } catch (err) {
        setDeleteError(err instanceof Error ? err.message : "Incorrect password. Account deletion failed.");
      } finally {
        setDeletingAccount(false);
      }
    }
    async function loadData(tab = selectedTab, sortMode = sortBy) {
      try {
        const boardPromise = tab === "global" ? api.leaderboard(userId, sortMode) : tab === "friends" ? api.friendsLeaderboard(userId, sortMode) : api.groupLeaderboard(tab, userId, sortMode);
        const [dashRes, myGroupsRes, boardRes, feedData] = await Promise.all([
          api.dashboard(userId).catch((err) => {
            if (err.message.includes("404") || err.message.includes("not found")) {
              onResetUser();
              return null;
            }
            throw err;
          }),
          api.myGroups(userId).catch(() => ({ groups: [] })),
          boardPromise.catch(() => null),
          fetch(`${API_BASE}/feed/recent-solves?limit=10`).then((res) => res.ok ? res.json() : []).catch(() => [])
        ]);
        if (!dashRes) {
          setBoardLoading(false);
          return;
        }
        setDash(dashRes);
        if (myGroupsRes?.groups) setGroups(myGroupsRes.groups);
        if (boardRes) {
          setBoard(boardRes);
          setTabBoards((prev) => ({ ...prev, [String(tab)]: boardRes }));
          setStored(`codestreak_cached_board_${String(tab)}`, JSON.stringify(boardRes));
          setStored("codestreak_cached_board", JSON.stringify(boardRes));
        }
        setBoardLoading(false);
        if (Array.isArray(feedData)) setActivityFeed(feedData);
        setError(null);
        setStored("codestreak_cached_dash", JSON.stringify(dashRes));
        if (typeof chrome !== "undefined" && chrome.action && chrome.action.setBadgeText) {
          const badgeText = dashRes.today_count > 0 ? `\u{1F525}${dashRes.current_streak}` : `${dashRes.current_streak}`;
          chrome.action.setBadgeText({ text: badgeText });
          chrome.action.setBadgeBackgroundColor({ color: dashRes.today_count > 0 ? "#10b981" : "#6366f1" });
        }
      } catch (err) {
        setBoardLoading(false);
        const errMsg = err instanceof Error ? err.message : "";
        if (errMsg.includes("404") || errMsg.includes("User not found")) {
          onResetUser();
        } else {
          setError(err instanceof Error ? err.message : "Couldn't load dashboard.");
        }
      }
    }
    async function handleToggleKudos(toUserId) {
      if (!userId || toUserId === userId) return;
      let previousCount = 0;
      let previousHasKudosed = false;
      setBoard((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          entries: prev.entries.map((e) => {
            if (e.id === toUserId) {
              previousCount = e.kudos_count || 0;
              previousHasKudosed = !!e.has_kudosed;
              const nextHasKudosed = !e.has_kudosed;
              const delta = nextHasKudosed ? 1 : -1;
              const nextCount = Math.max(0, previousCount + delta);
              return { ...e, kudos_count: nextCount, has_kudosed: nextHasKudosed };
            }
            return e;
          })
        };
      });
      try {
        const res = await api.toggleKudos(toUserId, userId);
        setBoard((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            entries: prev.entries.map(
              (e) => e.id === toUserId ? { ...e, kudos_count: res.kudos_count, has_kudosed: res.has_kudosed } : e
            )
          };
        });
      } catch (err) {
        console.error("Kudos background sync error, rolling back:", err);
        setBoard((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            entries: prev.entries.map(
              (e) => e.id === toUserId ? { ...e, kudos_count: previousCount, has_kudosed: previousHasKudosed } : e
            )
          };
        });
      }
    }
    async function fetchLeaderboardOnly(tab = selectedTab, sortMode = sortBy) {
      const tabKey = String(tab);
      if (tabBoards[tabKey]) {
        setBoard(tabBoards[tabKey]);
        setBoardLoading(false);
      } else {
        setBoard(null);
        setBoardLoading(true);
      }
      try {
        const boardPromise = tab === "global" ? api.leaderboard(userId, sortMode) : tab === "friends" ? api.friendsLeaderboard(userId, sortMode) : api.groupLeaderboard(tab, userId, sortMode);
        const boardRes = await boardPromise;
        if (boardRes) {
          setBoard(boardRes);
          setTabBoards((prev) => ({ ...prev, [tabKey]: boardRes }));
          setStored(`codestreak_cached_board_${tabKey}`, JSON.stringify(boardRes));
        }
      } catch (err) {
        console.error("Leaderboard fetch error:", err);
      } finally {
        setBoardLoading(false);
      }
    }
    (0, import_react.useEffect)(() => {
      if (userId) {
        loadData(selectedTab, sortBy);
      }
    }, [userId]);
    (0, import_react.useEffect)(() => {
      if (userId) {
        fetchLeaderboardOnly(selectedTab, sortBy);
      }
    }, [selectedTab, sortBy]);
    async function handleSync() {
      setSyncing(true);
      setSyncMsg(null);
      setError(null);
      try {
        const res = await api.syncUser(userId);
        await loadData();
        setSyncMsg(
          res.new_solves > 0 ? `Synced! ${res.new_solves} new solve(s) added.` : "LeetCode up to date!"
        );
        setTimeout(() => setSyncMsg(null), 3500);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Sync failed.");
      } finally {
        setSyncing(false);
      }
    }
    async function handleCreateGroup(e) {
      e.preventDefault();
      if (!newGroupName.trim()) return;
      setGroupActionBusy(true);
      try {
        const group = await api.createGroup(userId, newGroupName.trim());
        setNewGroupName("");
        setShowCreateGroup(false);
        changeTab(group.id);
        await loadData(group.id);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to create group.");
      } finally {
        setGroupActionBusy(false);
      }
    }
    async function handleJoinGroup(e) {
      e.preventDefault();
      if (!joinCode.trim()) return;
      setGroupActionBusy(true);
      try {
        const group = await api.joinGroup(userId, joinCode.trim());
        setJoinCode("");
        setShowJoinGroup(false);
        changeTab(group.id);
        await loadData(group.id);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to join group.");
      } finally {
        setGroupActionBusy(false);
      }
    }
    async function handleRemoveMember(groupId, memberUserId, memberName) {
      if (!confirm(`Are you sure you want to remove ${memberName} from this group?`))
        return;
      try {
        await api.removeMember(groupId, memberUserId, userId);
        await loadData(groupId);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not remove member.");
      }
    }
    async function handleInspectFriend(entry) {
      setInspectedFriend(entry);
      setModalTab("overview");
      setLoadingFriendDash(true);
      setLoadingRecentSolves(true);
      try {
        const [friendData, solvesData] = await Promise.all([
          api.dashboard(entry.id).catch(() => null),
          api.recentSolves(entry.id, 10).catch(() => [])
        ]);
        setFriendDash(friendData);
        setRecentSolvesList(solvesData);
      } catch (err) {
        console.warn("Could not load friend detailed data", err);
      } finally {
        setLoadingFriendDash(false);
        setLoadingRecentSolves(false);
      }
    }
    function handleCopyCode(code) {
      navigator.clipboard.writeText(code);
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2e3);
    }
    if (error && !dash) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "error-banner", children: error });
    if (!dash || !board) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "centered muted", children: "Loading data\u2026" });
    const maxDay = Math.max(1, ...dash.last_7_days.map((d) => d.problems_solved));
    const dayLabels = dash.last_7_days.map(
      (d) => new Date(d.date).toLocaleDateString(void 0, { weekday: "narrow" })
    );
    const activeGroup = selectedTab !== "global" && selectedTab !== "friends" ? groups.find((g) => String(g.id) === String(selectedTab)) : null;
    const isGroupOwner = Boolean(
      activeGroup && Number(activeGroup.creator_id) === Number(userId)
    );
    return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "dashboard", children: [
      /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "profile-bar", children: [
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "profile-info", children: [
          dash.avatar_url ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("img", { src: dash.avatar_url, alt: dash.name, className: "avatar" }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "avatar-placeholder", children: dash.name[0].toUpperCase() }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "profile-name", children: dash.name }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(
              "a",
              {
                href: `https://leetcode.com/u/${dash.leetcode_username}/`,
                target: "_blank",
                rel: "noreferrer",
                className: "profile-handle",
                children: [
                  "@",
                  dash.leetcode_username
                ]
              }
            )
          ] })
        ] }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "profile-actions", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
            "button",
            {
              className: "coffee-btn",
              onClick: () => setShowCoffeeModal(true),
              title: "Buy Me a Coffee \u2615",
              children: "\u2615"
            }
          ),
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
            "button",
            {
              className: "settings-btn",
              onClick: () => {
                setNewLeetcodeUsername(dash.leetcode_username);
                setSettingsMsg(null);
                setShowSettings(true);
              },
              title: "Account Settings (Change LeetCode Username)",
              children: "\u2699\uFE0F"
            }
          ),
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
            "button",
            {
              className: "rules-icon-btn",
              onClick: () => setShowPointsHelp(true),
              title: "Points System Rulebook \u2753",
              children: "\u2753"
            }
          ),
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
            "button",
            {
              className: "sync-btn",
              onClick: handleSync,
              disabled: syncing,
              title: "Force sync latest LeetCode activity",
              children: syncing ? "Syncing\u2026" : "\u{1F504} Sync"
            }
          )
        ] })
      ] }),
      isOffline && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "offline-banner", children: "\u26A0\uFE0F Connection lost \u2014 checking network\u2026" }),
      appConfig?.announcement && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "announcement-banner", children: [
        "\u{1F4E2} ",
        appConfig.announcement
      ] }),
      syncMsg && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "sync-banner", children: syncMsg }),
      error && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "error-banner", children: error }),
      toastSolve && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "solve-toast-popup", children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "toast-content", children: [
        /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "toast-flame", children: "\u{1F525}" }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "toast-text", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("strong", { children: toastSolve.user_name }),
          " just solved ",
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("strong", { children: [
            '"',
            toastSolve.title,
            '"'
          ] }),
          " on LeetCode!"
        ] }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
          "a",
          {
            href: toastSolve.leetcode_url,
            target: "_blank",
            rel: "noreferrer",
            className: "toast-link",
            children: "Open \u2197"
          }
        ),
        /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", { className: "toast-close", onClick: () => setToastSolve(null), children: "\u2715" })
      ] }) }),
      /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "hero-card", children: [
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "streak-hero", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "flame-icon", children: "\u{1F525}" }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "streak-count", children: dash.current_streak })
        ] }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "streak-label", children: "DAY STREAK" }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "stat-row", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Stat, { label: "Today", value: dash.today_count }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Stat, { label: "This Week", value: dash.weekly_total }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Stat, { label: "This Month", value: dash.monthly_total })
        ] }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "diff-pills", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", { className: "diff-pill easy", children: [
            "Easy ",
            dash.easy_count
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", { className: "diff-pill medium", children: [
            "Med ",
            dash.medium_count
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", { className: "diff-pill hard", children: [
            "Hard ",
            dash.hard_count
          ] })
        ] })
      ] }),
      /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "section", children: [
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "section-header", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "section-title", children: "Leaderboard" }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "group-btn-group", children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
              "button",
              {
                className: "chip-btn",
                onClick: () => setShowCreateGroup(!showCreateGroup),
                children: "+ Create Group"
              }
            ),
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
              "button",
              {
                className: "chip-btn",
                onClick: () => setShowJoinGroup(!showJoinGroup),
                children: "Join Code"
              }
            )
          ] })
        ] }),
        showCreateGroup && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", { className: "inline-form", onSubmit: handleCreateGroup, children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
            "input",
            {
              value: newGroupName,
              onChange: (e) => setNewGroupName(e.target.value),
              placeholder: "Group name (e.g. Code Bros)",
              autoFocus: true
            }
          ),
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", { type: "submit", className: "primary-btn sm", disabled: groupActionBusy, children: groupActionBusy ? "Creating\u2026" : "Create" })
        ] }),
        showJoinGroup && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", { className: "inline-form", onSubmit: handleJoinGroup, children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
            "input",
            {
              value: joinCode,
              onChange: (e) => setJoinCode(e.target.value),
              placeholder: "Invite code (e.g. STREAK-X79)",
              autoFocus: true
            }
          ),
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", { type: "submit", className: "primary-btn sm", disabled: groupActionBusy, children: groupActionBusy ? "Joining\u2026" : "Join" })
        ] }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "tab-bar-container", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
            "button",
            {
              className: `tab-btn ${selectedTab === "global" ? "active" : ""}`,
              onClick: () => changeTab("global"),
              title: "Global Leaderboard (All platform users)",
              children: "\u{1F310} Global"
            }
          ),
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
            "button",
            {
              className: `tab-btn ${selectedTab === "friends" ? "active" : ""}`,
              onClick: () => changeTab("friends"),
              title: "My Friends (All group members across your groups)",
              children: "\u{1F465} My Friends"
            }
          ),
          groups.map((g) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(
            "button",
            {
              className: `tab-btn ${selectedTab === g.id ? "active" : ""}`,
              onClick: () => changeTab(g.id),
              children: [
                "\u{1F465} ",
                g.name
              ]
            },
            g.id
          ))
        ] }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "sort-toggle-bar", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "sort-left-group", children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "sort-label", children: "Sort:" }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
              "button",
              {
                type: "button",
                className: "rules-chip-btn",
                onClick: () => setShowPointsHelp(true),
                title: "How Points Work \u2753",
                children: "\u2753 Rules"
              }
            ),
            /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "sort-btn-group", children: [
              /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
                "button",
                {
                  type: "button",
                  className: `sort-btn ${sortBy === "points" ? "active" : ""}`,
                  onClick: () => setSortBy("points"),
                  title: "Sort leaderboard by total points",
                  children: "\u2B50 Points"
                }
              ),
              /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
                "button",
                {
                  type: "button",
                  className: `sort-btn ${sortBy === "streak" ? "active" : ""}`,
                  onClick: () => setSortBy("streak"),
                  title: "Sort leaderboard by active daily streak",
                  children: "\u{1F525} Streak"
                }
              )
            ] })
          ] }),
          activeGroup && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(
            "button",
            {
              type: "button",
              className: "group-code-btn",
              onClick: () => handleCopyCode(activeGroup.code),
              title: `Click to copy invite code (${activeGroup.code})`,
              children: [
                "\u{1F4CB} ",
                copiedCode ? "Copied!" : "Code"
              ]
            }
          )
        ] }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("ul", { className: "leaderboard", children: [
          boardLoading || !board ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("li", { className: "leaderboard-skeleton-item", children: [
              /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "skeleton-avatar" }),
              /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "skeleton-line" })
            ] }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("li", { className: "leaderboard-skeleton-item", children: [
              /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "skeleton-avatar" }),
              /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "skeleton-line" })
            ] }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("li", { className: "leaderboard-skeleton-item", children: [
              /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "skeleton-avatar" }),
              /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "skeleton-line" })
            ] })
          ] }) : board.entries.length === 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("li", { className: "centered muted py-3", children: "No members in this group yet." }) : board.entries.map((e, index, arr) => {
            const prevEntry = index > 0 ? arr[index - 1] : null;
            const showGap = prevEntry && e.rank > prevEntry.rank + 1;
            return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_react.default.Fragment, { children: [
              showGap && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("li", { className: "leaderboard-gap", title: "Ranks between Top 10 and your position", children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "\u2022\u2022\u2022" }) }),
              /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(
                "li",
                {
                  className: `leaderboard-item ${e.id === userId ? "me" : ""}`,
                  children: [
                    /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(
                      "div",
                      {
                        className: "clickable-user",
                        onClick: () => handleInspectFriend(e),
                        title: "Click to view detailed friend stats",
                        children: [
                          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "rank", children: e.rank }),
                          e.avatar_url ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("img", { src: e.avatar_url, alt: e.name, className: "rank-avatar" }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "rank-avatar-placeholder", children: e.name[0] }),
                          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "name-col", children: [
                            /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "name-row", children: [
                              /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
                                "span",
                                {
                                  className: "dot",
                                  style: { opacity: e.is_active_today ? 1 : 0.25 },
                                  title: e.is_active_today ? "Solved today" : "Not solved today",
                                  children: "\u25CF"
                                }
                              ),
                              /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "name", children: e.name })
                            ] }),
                            /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", { className: "handle-mini", children: [
                              "@",
                              e.leetcode_username
                            ] })
                          ] }),
                          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", { className: "streak-mini", children: [
                            "\u{1F525}",
                            e.current_streak,
                            "d"
                          ] }),
                          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", { className: "solves-badge", title: "Questions solved this week", children: [
                            "\u{1F4DD}",
                            e.weekly_total
                          ] }),
                          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(
                            "span",
                            {
                              className: "points-badge",
                              title: `Easy: ${e.easy_count} | Medium: ${e.medium_count} | Hard: ${e.hard_count}`,
                              children: [
                                "\u2B50",
                                e.points !== null && e.points !== void 0 ? Math.round(e.points) : "\u2022\u2022\u2022"
                              ]
                            }
                          ),
                          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(
                            "button",
                            {
                              type: "button",
                              className: `kudos-badge ${e.has_kudosed ? "active" : ""} ${e.id === userId ? "disabled" : ""}`,
                              title: e.id === userId ? "Your active streak" : e.has_kudosed ? "Click to remove kudos (resets daily IST)" : "Click to give kudos (resets daily IST)",
                              onClick: (evt) => {
                                evt.stopPropagation();
                                handleToggleKudos(e.id);
                              },
                              children: [
                                "\u{1F44D} ",
                                e.kudos_count || 0
                              ]
                            }
                          )
                        ]
                      }
                    ),
                    isGroupOwner && Number(e.id) !== Number(userId) && activeGroup && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
                      "button",
                      {
                        type: "button",
                        className: "remove-btn",
                        onClick: (evt) => {
                          evt.stopPropagation();
                          handleRemoveMember(activeGroup.id, e.id, e.name);
                        },
                        title: `Remove ${e.name} from group`,
                        children: "\u{1F5D1}\uFE0F"
                      }
                    )
                  ]
                }
              )
            ] }, e.id);
          }),
          board && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [
            (board.total_users ?? 0) > (board.entries[board.entries.length - 1]?.rank ?? 0) && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("li", { className: "leaderboard-gap", title: "More registered users in squad", children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "\u2022\u2022\u2022" }) }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("li", { className: "leaderboard-total-row", children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: selectedTab === "global" ? `\u2694\uFE0F ${board.total_users ?? board.entries.length} algorithm warriors on leetstreak` : selectedTab === "friends" ? `\u{1F9E0} ${board.total_users ?? board.entries.length} algorithm compadres in your squad` : `\u2694\uFE0F ${board.total_users ?? board.entries.length} devs grinding in this group` }) })
          ] })
        ] })
      ] }),
      inspectedFriend && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "modal-overlay", onClick: () => setInspectedFriend(null), children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "modal-content", onClick: (e) => e.stopPropagation(), children: [
        /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
          "button",
          {
            className: "modal-close",
            onClick: () => setInspectedFriend(null),
            title: "Close modal",
            children: "\u2715"
          }
        ),
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "modal-header", children: [
          inspectedFriend.avatar_url && !avatarLoadError ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
            "img",
            {
              src: inspectedFriend.avatar_url,
              alt: inspectedFriend.name,
              className: "modal-avatar",
              onError: () => setAvatarLoadError(true)
            }
          ) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "avatar-placeholder lg", children: inspectedFriend.name ? inspectedFriend.name[0].toUpperCase() : "U" }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "modal-user-info", children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", { children: inspectedFriend.name }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(
              "a",
              {
                href: `https://leetcode.com/u/${inspectedFriend.leetcode_username}/`,
                target: "_blank",
                rel: "noreferrer",
                className: "profile-handle",
                children: [
                  "@",
                  inspectedFriend.leetcode_username,
                  " \u2197"
                ]
              }
            )
          ] })
        ] }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "modal-streak-box", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "flame-icon", children: "\u{1F525}" }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", { className: "modal-streak-count", children: [
            inspectedFriend.current_streak,
            " Day Streak"
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(
            "span",
            {
              className: "modal-points-tag",
              title: `Easy: ${inspectedFriend.easy_count} | Medium: ${inspectedFriend.medium_count} | Hard: ${inspectedFriend.hard_count}`,
              children: [
                "\u2B50 ",
                inspectedFriend.points ?? inspectedFriend.easy_count * 1 + inspectedFriend.medium_count * 3 + inspectedFriend.hard_count * 6,
                " pts"
              ]
            }
          )
        ] }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "modal-tab-bar", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
            "button",
            {
              className: `modal-tab-btn ${modalTab === "overview" ? "active" : ""}`,
              onClick: () => setModalTab("overview"),
              children: "\u{1F4CA} Overview"
            }
          ),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(
            "button",
            {
              className: `modal-tab-btn ${modalTab === "solves" ? "active" : ""}`,
              onClick: () => setModalTab("solves"),
              children: [
                "\u{1F4DD} Recent Solves (",
                recentSolvesList.length,
                ")"
              ]
            }
          )
        ] }),
        modalTab === "overview" ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "section-title text-center mb-1", children: "QUESTIONS SOLVED" }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "stat-row", children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
              Stat,
              {
                label: "Today",
                value: friendDash ? friendDash.today_count : inspectedFriend.is_active_today ? 1 : 0
              }
            ),
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Stat, { label: "This Week", value: inspectedFriend.weekly_total }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
              Stat,
              {
                label: "This Month",
                value: friendDash ? friendDash.monthly_total : 0
              }
            )
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "diff-pills", children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", { className: "diff-pill easy", children: [
              "Easy ",
              inspectedFriend.easy_count
            ] }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", { className: "diff-pill medium", children: [
              "Med ",
              inspectedFriend.medium_count
            ] }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", { className: "diff-pill hard", children: [
              "Hard ",
              inspectedFriend.hard_count
            ] })
          ] }),
          loadingFriendDash ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "centered muted tiny py-2", children: "Loading activity calendar\u2026" }) : friendDash ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "profile-calendar-card", children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "profile-calendar-title", children: [
              /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "\u{1F4C5}" }),
              /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "LAST 7 DAYS ACTIVITY" })
            ] }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "profile-heatmap", children: friendDash.last_7_days.map((d, i) => {
              const solved = d.problems_solved;
              const maxSolved = Math.max(1, ...friendDash.last_7_days.map((x) => x.problems_solved));
              const heightPct = Math.min(100, Math.max(14, solved / maxSolved * 100));
              return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "profile-heat-col", children: [
                /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "profile-bar-track", children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
                  "div",
                  {
                    className: `profile-heat-bar ${solved > 0 ? "active" : ""}`,
                    style: {
                      height: `${heightPct}%`
                    },
                    title: `${d.date}: ${solved} problem${solved === 1 ? "" : "s"} solved`
                  }
                ) }),
                /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "profile-heat-day", children: dayLabels[i] })
              ] }, d.date);
            }) })
          ] }) : null
        ] }) : /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "modal-solves-container", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "section-title mb-1", children: "Last 10 Solved Questions" }),
          loadingRecentSolves ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "centered muted tiny py-3", children: "Loading solves\u2026" }) : recentSolvesList.length === 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "centered muted tiny py-3", children: "No recent solves recorded yet." }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("ul", { className: "recent-solves-list", children: recentSolvesList.map((s, idx) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("li", { className: "solve-item", children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "solve-bullet", children: "\u2714" }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "solve-info", children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(
              "a",
              {
                href: s.leetcode_url,
                target: "_blank",
                rel: "noreferrer",
                className: "solve-title",
                children: [
                  s.title,
                  " \u2197"
                ]
              }
            ) }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "solve-time", children: s.relative_time })
          ] }, idx)) })
        ] })
      ] }) }),
      showSettings && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "modal-overlay", onClick: () => setShowSettings(false), children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "modal-content", onClick: (e) => e.stopPropagation(), children: [
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "modal-header", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", { children: "\u2699\uFE0F Account Settings" }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
            "button",
            {
              className: "modal-close",
              onClick: () => setShowSettings(false),
              title: "Close settings",
              children: "\u2715"
            }
          )
        ] }),
        settingsMsg && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "sync-banner", children: settingsMsg }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", { onSubmit: handleUpdateUsername, className: "modal-form", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "modal-field", children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", { children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "LeetCode Username" }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
              "input",
              {
                value: newLeetcodeUsername,
                onChange: (e) => setNewLeetcodeUsername(e.target.value),
                placeholder: "e.g. neal_wu",
                required: true
              }
            )
          ] }) }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
            "button",
            {
              type: "submit",
              className: "primary-btn modal-action-btn",
              disabled: updatingUsername,
              children: updatingUsername ? "Verifying & Updating\u2026" : "Save New Username"
            }
          )
        ] }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { style: { marginTop: "12px" }, children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
          "button",
          {
            type: "button",
            className: "secondary-btn modal-action-btn",
            onClick: () => {
              setShowSettings(false);
              onResetUser();
            },
            children: "\u{1F504} Switch User"
          }
        ) }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "danger-zone", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("hr", { className: "modal-divider" }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "danger-zone-header", children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "danger-zone-title", children: "Danger Zone" }) }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
            "button",
            {
              type: "button",
              className: "danger-btn modal-action-btn",
              onClick: () => {
                setShowSettings(false);
                setDeletePassword("");
                setDeleteError(null);
                setShowDeleteModal(true);
              },
              children: "\u{1F5D1}\uFE0F Delete Account"
            }
          )
        ] })
      ] }) }),
      showDeleteModal && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "modal-overlay", onClick: () => setShowDeleteModal(false), children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "modal-content", onClick: (e) => e.stopPropagation(), children: [
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "modal-header", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", { className: "danger-title", children: "\u{1F5D1}\uFE0F Delete Account" }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
            "button",
            {
              className: "modal-close",
              onClick: () => setShowDeleteModal(false),
              title: "Cancel",
              children: "\u2715"
            }
          )
        ] }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { className: "modal-description danger-text", children: "This action is permanent and cannot be undone. All your streaks, points, and group memberships will be deleted." }),
        deleteError && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "error-banner", children: deleteError }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", { onSubmit: handleDeleteAccount, className: "modal-form", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "modal-field", children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", { children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "Enter Password to Confirm" }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
              "input",
              {
                type: "password",
                value: deletePassword,
                onChange: (e) => setDeletePassword(e.target.value),
                placeholder: "Account password",
                required: true
              }
            )
          ] }) }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "modal-actions-row", children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
              "button",
              {
                type: "button",
                className: "secondary-btn",
                onClick: () => setShowDeleteModal(false),
                disabled: deletingAccount,
                children: "Cancel"
              }
            ),
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
              "button",
              {
                type: "submit",
                className: "danger-btn modal-action-btn",
                disabled: deletingAccount || !deletePassword,
                children: deletingAccount ? "Deleting\u2026" : "Confirm & Delete"
              }
            )
          ] })
        ] })
      ] }) }),
      showCoffeeModal && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "modal-overlay", onClick: () => setShowCoffeeModal(false), children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "modal-content coffee-modal", onClick: (e) => e.stopPropagation(), children: [
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "modal-header", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", { children: "\u2615 Buy Me a Coffee" }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)(
            "button",
            {
              className: "modal-close",
              onClick: () => setShowCoffeeModal(false),
              title: "Close modal",
              children: "\u2715"
            }
          )
        ] }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "coffee-modal-body", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "qr-container", children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("img", { src: "upi_qr.png", alt: "UPI QR Code", className: "upi-qr-img" }) }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "coffee-text-box", children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { className: "coffee-gratitude-title", children: "\u{1F49B} Thank you for using LeetStreak!" }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", { className: "coffee-gratitude-text", children: "If LeetStreak helps you and your friends stay consistent on LeetCode, consider buying me a coffee! Your support fuels server hosting, live features, and continuous updates. Every cup is deeply appreciated! \u2615" })
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "upi-badge-box", children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "tiny muted uppercase", children: "Scan with any UPI App" }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "upi-app-icons", children: "GPay \u2022 PhonePe \u2022 Paytm \u2022 BHIM" })
          ] })
        ] })
      ] }) })
    ] });
  }
  function Stat({ label, value }) {
    return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "stat", children: [
      /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "stat-value", children: value }),
      /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "tiny muted", children: label })
    ] });
  }
  function PointsHelpModal({ onClose }) {
    return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "modal-overlay", onClick: onClose, children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "modal-content points-help-modal", onClick: (e) => e.stopPropagation(), children: [
      /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "modal-header", children: [
        /* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", { children: "\u{1F3AF} Points System Rulebook" }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", { className: "modal-close", onClick: onClose, title: "Close rules", children: "\u2715" })
      ] }),
      /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "points-rules-container", children: [
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "rule-card", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "rule-card-title", children: "1\uFE0F\u20E3 Base Points (True Difficulty)" }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", { className: "rule-desc", children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("strong", { children: "Contest Questions:" }),
            " Points equal ",
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("code", { children: "Contest Rating / 100" }),
            " (e.g. 1550 rating = ",
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("strong", { children: "15.50 pts" }),
            ", 2400 rating = ",
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("strong", { children: "24.00 pts" }),
            ")."
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", { className: "rule-desc", children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("strong", { children: "Other Questions:" }),
            " Category Base (Easy: 10, Medium: 25, Hard: 45) dynamically adjusted by Acceptance Rate."
          ] })
        ] }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "rule-card", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "rule-card-title", children: "2\uFE0F\u20E3 Extra Bonuses" }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("ul", { className: "rule-list", children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("li", { children: [
              "\u{1F31F} ",
              /* @__PURE__ */ (0, import_jsx_runtime.jsx)("strong", { children: "LeetCode Daily Challenge:" }),
              " ",
              /* @__PURE__ */ (0, import_jsx_runtime.jsx)("code", { children: "+5.00 Bonus Pts" })
            ] }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("li", { children: [
              "\u26A1 ",
              /* @__PURE__ */ (0, import_jsx_runtime.jsx)("strong", { children: "First-Try Precision (0 Fails):" }),
              " ",
              /* @__PURE__ */ (0, import_jsx_runtime.jsx)("code", { children: "+3.00 Bonus Pts" })
            ] })
          ] })
        ] }),
        /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "rule-card", children: [
          /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "rule-card-title", children: "3\uFE0F\u20E3 Active Streak Multiplier" }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", { className: "rule-desc", children: [
            "Your total points scale linearly from ",
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("strong", { children: "1.0x" }),
            " (Day 1) up to ",
            /* @__PURE__ */ (0, import_jsx_runtime.jsx)("strong", { children: "1.10x" }),
            " (+10% max for 30+ day streak)."
          ] }),
          /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "streak-scale-grid", children: [
            /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "scale-item", children: [
              "Day 1: ",
              /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "1.00x" })
            ] }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "scale-item", children: [
              "Day 15: ",
              /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "1.05x" })
            ] }),
            /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { className: "scale-item", children: [
              "Day 30+: ",
              /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "1.10x (Max)" })
            ] })
          ] })
        ] })
      ] }),
      /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "modal-actions-row", children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", { type: "button", className: "primary-btn sm block-btn", onClick: onClose, children: "Got it!" }) })
    ] }) });
  }
})();
/*! Bundled license information:

react/cjs/react.development.js:
  (**
   * @license React
   * react.development.js
   *
   * Copyright (c) Facebook, Inc. and its affiliates.
   *
   * This source code is licensed under the MIT license found in the
   * LICENSE file in the root directory of this source tree.
   *)

react/cjs/react-jsx-runtime.development.js:
  (**
   * @license React
   * react-jsx-runtime.development.js
   *
   * Copyright (c) Facebook, Inc. and its affiliates.
   *
   * This source code is licensed under the MIT license found in the
   * LICENSE file in the root directory of this source tree.
   *)
*/
