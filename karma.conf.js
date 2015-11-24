// Karma configuration

module.exports = function(config) {
  config.set({

    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: 'openassessment/xblock/static/js',


    plugins: [
      'karma-jasmine',
      'karma-jasmine-jquery',
      'karma-chrome-launcher',
      'karma-phantomjs-launcher',
      'karma-junit-reporter',
      'karma-coverage',
      'karma-sinon',
      'karma-jasmine-html-reporter',
      'karma-spec-reporter'
    ],

    // frameworks to use
    // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
    frameworks: ['jasmine-jquery', 'jasmine', 'sinon'],


    // list of files / patterns to load in the browser
    files: [
      'lib/jquery.min.js',
      'lib/*.js',
      'src/oa_shared.js',
      'src/*.js',
      'src/lms/*.js',
      'src/studio/*.js',
      'spec/test_shared.js',
      'spec/*.js',
      'spec/lms/*.js',
      'spec/studio/*.js',

      // fixtures
      {
        pattern: 'fixtures/*.html',
        served: true, included: false
      }
    ],


    // list of files to exclude
    exclude: [
      'spec/lms/oa_grade.js',  // due to EDX-521: Disable Feedback on Peer Assessments
      'src/design*.js'
    ],


    // preprocess matching files before serving them to the browser
    // available preprocessors: https://npmjs.org/browse/keyword/karma-preprocessor
    preprocessors: {
      'src/*.js': 'coverage',
      'src/lms/*.js': 'coverage',
      'src/studio/*.js': 'coverage'
    },


    // test results reporter to use
    // possible values: 'dots', 'progress', 'coverage', 'junit'
    // available reporters: https://npmjs.org/browse/keyword/karma-reporter
    reporters: ['progress','coverage','junit'],

    coverageReporter: {
      reporters: [
        {
          type : 'text'
        },
        {
          dir : 'coverage',
          type : 'cobertura',
          file : 'coverage.xml'
        }
      ]
    },

    junitReporter: {
        outputFile : 'xunit.xml',
        suite : 'JavaScript'
    },

    // web server port
    port: 9876,


    // enable / disable colors in the output (reporters and logs)
    colors: true,


    // level of logging
    // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
    logLevel: config.LOG_INFO,


    // enable / disable watching file and executing tests whenever any file changes
    autoWatch: false,

    // start these browsers
    // available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
    browsers: ['PhantomJS'],

    // Continuous Integration mode
    // if true, Karma captures browsers, runs the tests and exits
    singleRun: true

  });

};
