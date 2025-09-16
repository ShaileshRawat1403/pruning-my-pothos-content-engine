<?php
/*
Template Name: Gallery Page
*/
get_header();
?>

<section class="gallery-hero fade-in">
  <div class="container">
    <h1 class="gallery-title">The Visual Vine</h1>
    <p class="gallery-subtitle">Clicks, Curiosities, Creativity and Calm in Frames.</p>
  </div>
</section>

<section class="gallery-section">
  <div class="container">
    <section class="gallery-carousel-section">
      <div class="gallery-carousel infinite-loop">
        <?php
        $images = [];

        // ✅ Step 1: Try pulling from 'gallery_image' custom post type
        $custom_gallery_query = new WP_Query([
          'post_type' => 'gallery_image',
          'posts_per_page' => -1,
          'orderby' => 'date',
          'order' => 'DESC'
        ]);

        if ($custom_gallery_query->have_posts()) {
          while ($custom_gallery_query->have_posts()) {
            $custom_gallery_query->the_post();
            $img_url = get_the_post_thumbnail_url(get_the_ID(), 'large');
            $img_alt = get_the_title();
            $img_caption = get_the_excerpt();

            if (!$img_url) continue;

            $images[] = [
              'url'     => esc_url($img_url),
              'alt'     => esc_attr($img_alt),
              'caption' => esc_html($img_caption)
            ];
          }
          wp_reset_postdata();
        }

        // ✅ Step 2: Fallback to ACF repeater field
        if (empty($images) && function_exists('get_field')) {
          $acf_images = get_field('gallery_images', get_the_ID());
          if ($acf_images) {
            foreach ($acf_images as $acf_img) {
              if (!isset($acf_img['image']['url'])) continue;

              $images[] = [
                'url'     => esc_url($acf_img['image']['url']),
                'alt'     => esc_attr($acf_img['image']['alt'] ?? ''),
                'caption' => esc_html($acf_img['caption'] ?? '')
              ];
            }
          }
        }

        // ✅ Step 3: Fallback to hardcoded images
        if (empty($images)) {
          $images = [
            [
              'url' => 'https://pruningmypothos.com/wp-content/uploads/2025/03/26936489543_d8bd66a7e6.jpg',
              'alt' => 'Description 1',
              'caption' => 'A quiet morning leaf curl.'
            ],
            [
              'url' => 'https://pruningmypothos.com/wp-content/uploads/2025/03/Ananya-Kuttush-and-Simba-scaled-e1743319196841.jpg',
              'alt' => 'Ananya, Kuttush, and Simba',
              'caption' => 'Chaos, calm, and cuddles in one frame.'
            ],
            [
              'url' => 'https://pruningmypothos.com/wp-content/uploads/2025/03/Simba-and-Kuttush-scaled.jpg',
              'alt' => 'Simba and Kuttush',
              'caption' => 'Guardians of the plant galaxy.'
            ],
            [
              'url' => 'https://pruningmypothos.com/wp-content/uploads/2025/03/Kuttush-Young-scaled.jpg',
              'alt' => 'Kuttush Young',
              'caption' => 'Before he stole the pothos. Baby steps to betrayal.'
            ],
          ];
        }

        // ✅ Output gallery cards
        foreach ($images as $img) {
          if (empty($img['url'])) continue;

          echo '<div class="gallery-card" data-img="' . $img['url'] . '" data-caption="' . $img['caption'] . '">';
          echo '  <img src="' . $img['url'] . '" alt="' . $img['alt'] . '">';
          echo '  <div class="gallery-caption">' . $img['caption'] . '</div>';
          echo '</div>';
        }
        ?>
      </div>
    </section>
  </div>
</section>

<!-- ✅ MODAL FOR IMAGE VIEW -->
<div id="modal" class="gallery-modal">
  <span class="gallery-modal-close">&times;</span>
  <div class="gallery-modal-content">
    <img id="modal-img" src="" alt="">
    <p id="modal-caption"></p>
  </div>
</div>

<?php get_footer(); ?>
