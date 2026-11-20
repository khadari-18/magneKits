% Set up input and output video objects
vid1 = VideoReader('C:\Users\hilllab\Desktop\3DFM\data\2026-06-15\2-5MSuc_1um_Newset2_7rep_40x\img_2026-06-15-215205-0000.avi');
vid2 = VideoReader('C:\Users\hilllab\Desktop\3DFM\data\2026-06-15\2-5MSuc_1um_Newset2_7rep_40x\img_2026-06-15-215205-0001.avi');
outputVideo = VideoWriter('C:\Users\hilllab\Desktop\3DFM\data\2026-06-15\2-5MSuc_1um_Newset2_7rep_40x\merged_video.avi');

% Match the frame rate of the output to the first video
outputVideo.FrameRate = vid1.FrameRate;
open(outputVideo);

% Get the size of the first video to standardize frames
% sz1 = [vid1.Height vid1.Width];

% 1. Process and write frames from the first video
while hasFrame(vid1)
    img = readFrame(vid1);
    writeVideo(outputVideo, img);
end

% 2. Process and write frames from the second video
while hasFrame(vid2)
    img = readFrame(vid2);
    % 
    % % Resize the frame if it doesn't match the first video's dimensions
    % sz2 = [size(img, 1), size(img, 2)];
    % if ~isequal(sz1, sz2)
    %     img = imresize(img, sz1, 'bilinear');
    % end
    % 
    writeVideo(outputVideo, img);
end

% Clean up and close the output stream
close(outputVideo);
disp('Videos successfully merged!');
