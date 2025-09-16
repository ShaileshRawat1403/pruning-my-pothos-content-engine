<?php
/**
 * Theme Functions
 */

// 1. THEME SETUP
function myboho_theme_setup() {
    add_theme_support('post-thumbnails');
    add_theme_support('title-tag');
    // You can add more theme supports as needed:
    // add_theme_support('custom-logo');
    // add_theme_support('menus');
}
add_action('after_setup_theme', 'myboho_theme_setup');

// 2. ENQUEUE STYLES & SCRIPTS
function myboho_enqueue_assets() {
    // ✅ Google Fonts: Manrope & Space Grotesk (modern fonts)
    wp_enqueue_style(
        'google-fonts',
        'https://fonts.googleapis.com/css2?family=Manrope:wght@400;600&family=Space+Grotesk:wght@400;600&display=swap',
        false
    );

    // ✅ Main stylesheet
    wp_enqueue_style('myboho-style', get_stylesheet_uri(), array(), '1.0');
    
    wp_enqueue_style('font-awesome', 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css');

    // ✅ Custom JS (no jQuery dependency)
    wp_enqueue_script('myboho-custom-js', get_template_directory_uri() . '/custom.js', array(), '1.0', true);

    // ✅ AJAX support (optional - for load more posts)
    wp_localize_script('myboho-custom-js', 'ajaxObject', [
        'ajaxurl' => admin_url('admin-ajax.php'),
        'nonce'   => wp_create_nonce('myboho_load_more_nonce')
    ]);
}
add_action('wp_enqueue_scripts', 'myboho_enqueue_assets');

// 3. AJAX LOAD MORE POSTS
add_action('wp_ajax_myboho_load_more', 'myboho_load_more');
add_action('wp_ajax_nopriv_myboho_load_more', 'myboho_load_more');

function myboho_load_more() {
    check_ajax_referer('myboho_load_more_nonce', 'nonce');

    $offset   = intval($_POST['offset']);
    $ppp      = intval($_POST['ppp']);
    $category = sanitize_text_field($_POST['category'] ?? '');
    $search   = sanitize_text_field($_POST['s'] ?? '');

    $args = [
        'post_type'      => 'post',
        'posts_per_page' => $ppp,
        'offset'         => $offset
    ];

    if (!empty($category)) {
        $args['category_name'] = $category;
    }

    if (!empty($search)) {
        $args['s'] = $search;
    }

    $query = new WP_Query($args);

    if ($query->have_posts()) {
        ob_start();
        while ($query->have_posts()) {
            $query->the_post(); ?>
            <article class="post-card">
                <?php if (has_post_thumbnail()) : ?>
                    <a href="<?php the_permalink(); ?>">
                        <?php the_post_thumbnail('medium', ['loading' => 'lazy']); ?>
                    </a>
                <?php endif; ?>
                <h2 class="post-title"><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
                <p><?php echo wp_trim_words(get_the_excerpt(), 20); ?></p>
            </article>
        <?php }
        wp_reset_postdata();

        wp_send_json_success([
            'html'   => ob_get_clean(),
            'offset' => $offset + $ppp
        ]);
    } else {
        wp_send_json_error('No more posts');
    }

    wp_die();
}

// 4. CONTACT FORM HANDLER (if you need it)
add_action('admin_post_process_contact_form', 'process_contact_form');
add_action('admin_post_nopriv_process_contact_form', 'process_contact_form');

function process_contact_form() {
    if (!isset($_POST['name'], $_POST['email'], $_POST['message'])) {
        wp_die('Invalid form submission.');
    }

    $name    = sanitize_text_field($_POST['name']);
    $email   = sanitize_email($_POST['email']);
    $message = sanitize_textarea_field($_POST['message']);

    $to      = get_option('admin_email');
    $subject = "New Contact Form Submission from $name";
    $headers = "From: $name <$email>\r\n";
    $body    = "Name: $name\nEmail: $email\n\nMessage:\n$message";

    wp_mail($to, $subject, $body, $headers);

    wp_redirect(home_url('/contact/?success=1'));
    exit;
}

// 5. REGISTER CUSTOM POST TYPE: GALLERY IMAGES (Future-Proof)
function pruningmypothos_register_gallery_cpt() {
  $labels = array(
    'name'               => 'Gallery Images',
    'singular_name'      => 'Gallery Image',
    'add_new'            => 'Add New Image',
    'add_new_item'       => 'Add New Gallery Image',
    'edit_item'          => 'Edit Gallery Image',
    'new_item'           => 'New Gallery Image',
    'view_item'          => 'View Image',
    'search_items'       => 'Search Images',
    'not_found'          => 'No gallery images found',
    'not_found_in_trash' => 'No images found in Trash',
    'menu_name'          => 'Gallery Images',
  );

  $args = array(
    'labels'             => $labels,
    'public'             => true,
    'menu_icon'          => 'dashicons-format-image',
    'supports'           => array('title', 'thumbnail', 'excerpt'),
    'has_archive'        => false,
    'rewrite'            => false,
    'show_in_rest'       => true,
  );

  register_post_type('gallery_image', $args);
}
add_action('init', 'pruningmypothos_register_gallery_cpt');
