<?php
if (post_password_required()) return;
?>

<div id="comments" class="comments-area">
  <?php if (have_comments()) : ?>
    <h2 class="comments-title">
      <?php comments_number('No Comments', 'One Comment', '% Comments'); ?>
    </h2>
    <ul class="comment-list">
      <?php wp_list_comments(); ?>
    </ul>
    <?php paginate_comments_links(); ?>
  <?php endif; ?>

  <?php comment_form(); ?>
</div>
