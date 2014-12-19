<?php

/**
 * @file
 * Provide views data and handlers for salsa_archive module.
 *
 */

/**
 * Implements hook_views_data().
 */
function salsa_archive_views_data() {
  $data = array();
  $data['salsa_archive']['table']['group'] = t('SALSA archive table');
  
  // Advertise this table as a possible base table
  $data['salsa_archive']['table']['base'] = array(
    'field' => 'id',
    'title' => t('SALSA archive'),
  );
  $data['salsa_archive']['table']['join'] = array(
      'users' => array(
          'left_field' => 'name',
          'field' => 'observer',
      ),
  );

  // field id
  $data['salsa_archive']['id'] = array(
    'title' => t('Id'),
    'help' => t('The observation ID.'), // The help that appears on the UI,
    // Information for displaying the nid
    'field' => array(
      'handler' => 'views_handler_field',
      'click sortable' => TRUE,
    ),
    // Information for accepting a id as a filter
    'filter' => array(
      'handler' => 'views_handler_filter_numeric',
    ),
    // Information for sorting on a id.
    'sort' => array(
      'handler' => 'views_handler_sort',
    ),
    'argument' => array(
      'handler' => 'views_handler_argument_numeric',
    ),
  );

  // field observer
  $data['salsa_archive']['observer'] = array(
    'title' => t('Observer'), 
    'help' => t('The user who uploaded this observation.'), 
    'field' => array(
      'handler' => 'views_handler_field', 
      'click sortable' => TRUE, // This is use by the table display plugin.
    ), 
    'sort' => array(
      'handler' => 'views_handler_sort',
    ), 
    'filter' => array(
      'handler' => 'views_handler_filter_string',
    ), 
    'argument' => array(
      'handler' => 'views_handler_argument_string',
    ),
    'relationship' => array(
      'base' => 'users',
      'field' => 'observer',
      'handler' => 'views_handler_relationship',
      'label' => t('Users/observer relationship'),
    ),
  );
 // field glon
  $data['salsa_archive']['glon'] = array(
    'title' => t('Galactic longitude'), 
    'help' => t('Value of galactic longitude observed here.'), 
    'field' => array(
      'handler' => 'views_handler_field', 
      'click sortable' => TRUE,
    ), 
    'filter' => array(
      'handler' => 'views_handler_filter_string',
    ), 
    'sort' => array(
      'handler' => 'views_handler_sort',
    ),
    'argument' => array(
      'handler' => 'views_handler_argument_string',
    ),
  );
  // Glat
  $data['salsa_archive']['glat'] = array(
    'title' => t('Galactic latitude'), 
    'help' => t('Value of galactic latitude observed here.'), 
    'field' => array(
      'handler' => 'views_handler_field', 
      'click sortable' => TRUE,
    ), 
    'filter' => array(
      'handler' => 'views_handler_filter_string',
    ), 
    'sort' => array(
      'handler' => 'views_handler_sort',
    ),
    'argument' => array(
      'handler' => 'views_handler_argument_string',
    ),
  );

  // Example timestamp field.
  $data['salsa_archive']['obsdate'] = array(
    'title' => t('Observation date and time.'), 
    'help' => t('Time in UTC when this observation was made.'), 
    'field' => array(
      'handler' => 'views_handler_field_date', 
      'click sortable' => TRUE,
    ), 
    'sort' => array(
      'handler' => 'views_handler_sort_date',
    ), 
    'filter' => array(
      'handler' => 'views_handler_filter_date',
    ),
  );

  // Example numeric text field.
  $data['salsa_archive']['obsfreq'] = array(
    'title' => t('Obs. frequency.'), 
    'help' => t('Frequency at which this observation was made.'), 
    'field' => array(
      'handler' => 'views_handler_field_numeric', 
      'click sortable' => TRUE,
    ), 
    'filter' => array(
      'handler' => 'views_handler_filter_numeric',
    ), 
    'sort' => array(
      'handler' => 'views_handler_sort',
    ),
  );
  
// Example numeric text field.
  $data['salsa_archive']['bandwidth'] = array(
    'title' => t('Obs. bandwidth.'), 
    'help' => t('Bandwidth recorded in this observation was made.'), 
    'field' => array(
      'handler' => 'views_handler_field_numeric', 
      'click sortable' => TRUE,
    ), 
    'filter' => array(
      'handler' => 'views_handler_filter_numeric',
    ), 
    'sort' => array(
      'handler' => 'views_handler_sort',
    ),
  );
  
// Example numeric text field.
  $data['salsa_archive']['int_time'] = array(
    'title' => t('Obs. integration time.'), 
    'help' => t('Total integration time (including switching).'), 
    'field' => array(
      'handler' => 'views_handler_field_numeric', 
      'click sortable' => TRUE,
    ), 
    'filter' => array(
      'handler' => 'views_handler_filter_numeric',
    ), 
    'sort' => array(
      'handler' => 'views_handler_sort',
    ),
  );
  
// Example plain text field.
  $data['salsa_archive']['telescope'] = array(
    'title' => t('Telescope'), 
    'help' => t('The telescope used in this observation.'), 
    'field' => array(
      'handler' => 'views_handler_field', 
      'click sortable' => TRUE, // This is use by the table display plugin.
    ), 
    'sort' => array(
      'handler' => 'views_handler_sort',
    ), 
    'filter' => array(
      'handler' => 'views_handler_filter_string',
    ), 
    'argument' => array(
      'handler' => 'views_handler_argument_string',
    ),
  );


  return $data;
}
